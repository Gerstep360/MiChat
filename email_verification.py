# email_verification.py

import smtplib
import ssl
from email.message import EmailMessage
import os
from dotenv import load_dotenv

# Cargar las variables de entorno desde el archivo .env
load_dotenv()

def send_verification_email(receiver_email, verification_code):
    sender_email = os.getenv('EMAIL_USER')
    password = os.getenv('EMAIL_PASSWORD')

    message = EmailMessage()
    message.set_content(f'Tu código de verificación es: {verification_code}')
    message['Subject'] = 'Código de Verificación'
    message['From'] = sender_email
    message['To'] = receiver_email

    context = ssl.create_default_context()

    with smtplib.SMTP_SSL('smtp.gmail.com', 465, context=context) as server:
        server.login(sender_email, password)
        server.send_message(message)
