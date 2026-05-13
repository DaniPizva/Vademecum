import smtplib

from email.message import EmailMessage

from os import getenv

from dotenv import load_dotenv

load_dotenv()

SMTP_SERVER = "smtp.gmail.com"
SMTP_PORT = 587

MAIL_USERNAME = getenv("MAIL_USERNAME")
MAIL_PASSWORD = getenv("MAIL_PASSWORD")
MAIL_FROM = getenv("MAIL_FROM")


def send_new_user_email(
    to_email: str,
    full_name: str,
    temp_password: str,
    verification_code: str
):

    subject = "Bienvenido al sistema"

    body = f"""
Hola {full_name},

Tu cuenta ha sido creada exitosamente.

Correo:
{to_email}

Contraseña temporal:
{temp_password}

Código de verificación:
{verification_code}

Por seguridad, deberás cambiar tu contraseña
al ingresar al sistema.

Si no solicitaste esta cuenta, ignora este mensaje.
"""

    msg = EmailMessage()

    msg["Subject"] = subject
    msg["From"] = MAIL_FROM
    msg["To"] = to_email

    msg.set_content(body)

    with smtplib.SMTP(
        SMTP_SERVER,
        SMTP_PORT
    ) as server:

        server.starttls()

        server.login(
            MAIL_USERNAME,
            MAIL_PASSWORD
        )

        server.send_message(msg)