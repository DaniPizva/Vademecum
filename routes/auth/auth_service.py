# routes\auth\auth_service.py

from typing import Any, Dict, Tuple, Optional
from flask import request
from contextlib import contextmanager
from db.db import SessionLocal
from werkzeug.security import check_password_hash, generate_password_hash
from db.models import User, Users_roles, Roles
from sqlalchemy.exc import IntegrityError
import re
import secrets
import string
from datetime import datetime, timezone


def checkemail(email: str):
    pattern = r'^[A-Za-z0-9._%+-]+@(uces\.edu\.co|ces\.edu\.co)$'
    if not re.match(pattern, email):
        raise ValueError('Email must end with "uces.edu.co" or "ces.edu.co".')


def generate_temp_password(length=12):
    """Generate a secure random temporary password."""
    alphabet = string.ascii_letters + string.digits
    return ''.join(secrets.choice(alphabet) for _ in range(length))


@contextmanager
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def loginUser(data):
    email = data.get("email", "").strip()
    password = data.get("password", "").strip()

    if not email or not password:
        return None, {"Credenciales": "Email y password son requeridas"}

    with get_db() as db:
        user = db.query(User).filter(User.email == email).first()
        if not user:
            return None, {"message": "User not found"}
        if not user.is_active:
            return None, {"message": "User is NOT active"}
        if not check_password_hash(user.password_hash, password):
            return None, {"message": "Incorrect password, try again"}

        # Set first login timestamp if it's the very first time
        if user.first_login_at is None:
            user.first_login_at = datetime.now(timezone.utc)
            db.commit()

        # Obtain role (first matching, as per current design)
        role_entry = db.query(Users_roles).filter(Users_roles.user_id == user.id).first()
        role_id = role_entry.role_id if role_entry else None

        response = {
            "id": user.id,
            "full_name": user.full_name,
            "email": user.email,
            "role_id": role_id,
            "terms_accepted": user.terms_accepted,
            "must_change_password": user.must_change_password,
        }
        return response, None


def createUser(data: Dict[str, Any]) -> Tuple[Optional[User], Any]:
    """Public registration: auto-generates a temporary password."""
    email = (data.get("email") or "").strip()
    full_name = (data.get("full_name") or "").strip()
    role_id = data.get("role_id")
    identification = data.get("identification")

    if not email or not full_name or not role_id or not identification:
        return None, {"error": "email, full_name, role_id y identification son requeridos"}

    checkemail(email)

    # Generate a random temporary password (will be sent via email)
    temp_password = generate_temp_password()

    with get_db() as db:
        try:
            # Check duplication
            if db.query(User).filter(User.email == email).first():
                return None, {"email": "Ya existe un usuario con ese correo"}

            # Validate role
            if not db.query(Roles).filter(Roles.id == role_id).first():
                return None, {"role_id": "El rol especificado no existe"}

            # Create user with lifecycle defaults
            user = User(
                email=email,
                full_name=full_name,
                identification=identification,
                password_hash=generate_password_hash(temp_password),
                terms_accepted=False,
                must_change_password=True,
                is_active=1
                # first_login_at and password_changed_at default to NULL
            )
            db.add(user)
            db.flush()  # get user.id

            # Assign role
            user_role = Users_roles(user_id=user.id, role_id=role_id)
            db.add(user_role)

            db.commit()
            db.refresh(user)

            # TODO: Send temp_password to user via email (integration point)
            # send_temp_password_email(user.email, temp_password)

            # Do NOT return the password in the response
            return {
                "user": user,
                "temp_password": temp_password
            }, None

        except IntegrityError as e:
            db.rollback()
            return None, {"db_error": str(e)}

#Función que actualiza el estado de terminos y condiciones
def accept_terms(user_id: int) -> Tuple[bool, Any]:
    """Mark terms as accepted for the given user."""
    with get_db() as db:
        user = db.query(User).filter(User.id == user_id).first()
        if not user:
            return False, {"message": "User not found"}
        user.terms_accepted = True
        db.commit()
        return True, None

#Función para el cambio de contraseña forzado en usuarios nuevos
def change_password(user_id: int, data: Dict[str, Any]) -> Tuple[bool, Any]:
    """
    Change user password. If must_change_password is True, current_password is not required.
    Otherwise, validate current_password before updating.
    """
    new_password = (data.get("new_password") or "").strip()
    current_password = (data.get("current_password") or "").strip()

    if not new_password:
        return False, {"message": "new_password es requerido"}

    with get_db() as db:
        user = db.query(User).filter(User.id == user_id).first()
        if not user:
            return False, {"message": "User not found"}

        # If the password is still system-generated, no current password needed
        if not user.must_change_password:
            # Normal change: verify current password
            if not current_password:
                return False, {"message": "current_password es requerido"}
            if not check_password_hash(user.password_hash, current_password):
                return False, {"message": "Contraseña actual incorrecta"}

        # Perform update
        user.password_hash = generate_password_hash(new_password)
        user.must_change_password = False
        user.password_changed_at = datetime.now(timezone.utc)
        db.commit()
        return True, None

#Función que actualiza el estado del usuario.
def get_me(user_id: int) -> Tuple[Optional[Dict], Any]:
    """Return current user's state for route guards (terms, password lifecycle)."""
    with get_db() as db:
        user = db.query(User).filter(User.id == user_id).first()
        if not user:
            return None, {"message": "User not found"}

        role_entry = db.query(Users_roles).filter(Users_roles.user_id == user.id).first()
        role_id = role_entry.role_id if role_entry else None

        return {
            "id": user.id,
            "email": user.email,
            "role_id": role_id,
            "terms_accepted": user.terms_accepted,
            "full_name": user.full_name,
            "must_change_password": user.must_change_password,
        }, None