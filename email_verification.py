# email_verification.py

import smtplib
import ssl
from email.message import EmailMessage

def send_verification_email(receiver_email, verification_code):
    sender_email = 'gersoft.official@gmail.com'
    password = 'hckn zfaq fgez jyoe'

    message = EmailMessage()
    message.set_content(f'Tu código de verificación es: {verification_code}')
    message['Subject'] = 'Código de Verificación'
    message['From'] = sender_email
    message['To'] = receiver_email

    context = ssl.create_default_context()

    with smtplib.SMTP_SSL('smtp.gmail.com', 465, context=context) as server:
        server.login(sender_email, password)
        server.send_message(message)
