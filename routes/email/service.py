# routes\auth\email\service.py
from routes.email.sender import _send_email
from dotenv import load_dotenv
from os import getenv 
load_dotenv()

FRONTEND_URL =getenv('FRONTEND_URL')

def send_new_user_email(
    to_email: str,
    full_name: str,
    temp_password: str,
    verification_code: str
):

    subject = "Bienvenido a VadeMecum"

    body = f"""
        Hola {full_name},

        Hemos recibido tu solicitud de registro y nos complace informarte que tu cuenta ha sido creada exitosamente.

        Podrás acceder utilizando:

        Correo:
        {to_email}

        Contraseña temporal:
        {temp_password}

        Código de verificación:
        {verification_code}

        Por motivos de seguridad deberás cambiar la contraseña temporal al ingresar por primera vez al sistema.

        Si no solicitaste esta cuenta, ignora este correo y comunícate con el administrador.
        """

    _send_email(
        to_email,
        subject,
        body
    )
    
def send_password_reset_email(
    to_email: str,
    full_name: str,
    verification_code: str
):

    subject = "Recuperación de contraseña - VadeMecum"

    reset_link = (
        f"{FRONTEND_URL}/reset-password"
    )

    body = f"""
    Hola {full_name},

    Hemos recibido una solicitud para restablecer la contraseña asociada a tu cuenta de VadeMecum.

    Para continuar y acceder al formulario desde el siguiente enlace:

    {reset_link}

    Código de verificación:

    {verification_code}

    Tendras que introducir este código el cual será válido durante 15 minutos, si este tiempo es superado, deberas realizar otra solicitud.

    Si usted no realizo esta solicitud, por favor comuniquese con nuestro soporte tecnico, ya que puede que su cuenta este comprometida. 
    """

    _send_email(
        to_email,
        subject,
        body
    )