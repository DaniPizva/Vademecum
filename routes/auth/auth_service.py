# routes\auth\auth_service.py
from typing import Any,Dict,List,Tuple, Optional
from flask import request
from contextlib import contextmanager
from db.db import SessionLocal
from werkzeug.security import check_password_hash, generate_password_hash
from db.models import User, Users_roles, Roles
from sqlalchemy.exc import IntegrityError
import re


def checkemail(email: str):
    pattern = r'^[A-Za-z0-9._%+-]+@(uces\.edu\.co|ces\.edu\.co)$'
    if not re.match(pattern, email):
        raise ValueError(f'Email must end with "uces.edu.co" or "ces.edu.co".')

@contextmanager
def get_db():
        db = SessionLocal()
        try:
            yield db  #mientras que se consulte se mantenga en la operacion
        finally:
            db.close()

def loginUser(data): #flecha es lo que devuelve
    email = data.get("email","")
    password = data.get("password" , "")
    password = password.strip()

    if not email or not password:
         return None, {"Credenciales": "Cedula y password son requeridas"}
     
    
    
    with get_db() as db:
        user = db.query(User).filter(User.email == email).first() 
        if not user:
            return None, {"message": "User not found"}
        if not user.is_active:
            return None, {"message": "User is NOT active"}
        if not check_password_hash(user.password_hash, password):
            return None, {"message": "Incorrect password, try again"}
          
        #Bloque de obtención del rol
        role_entry = db.query(Users_roles).filter(Users_roles.user_id == user.id).first()
        role_id = role_entry.role_id if role_entry else None

        
        user = {
            "id": user.id,
            "full_name": user.full_name,
            "email": user.email,
            "role_id": role_id
        }
        
        return user, None
     
def createUser(data: Dict[str, Any]) -> Tuple[Optional[User], Any]:
    """Útil para pruebas (semilla). Crea un usuario con contraseña hasheada."""
    email = (data.get("email") or "").strip()
    password = data.get("password") or ""
    full_name = (data.get("full_name") or "").strip()
    role_id = (data.get("role_id" or ""))
    identification = (data.get("identification" or ""))
 
    if not email or not password or not role_id or not identification:
        return None, {"email/password": "email, role_id y password son requeridos"}
    
    # Chequeo de la estructura del email.
    checkemail(email)
    
    with get_db() as db:
        try:
            # Verificar si el usuario ya existe
            exists = db.query(User).filter(User.email == email).first()
            if exists:
                return None, {"email": "Ya existe un usuario con ese correo"}

            # (Opcional pero recomendable) verificar que el rol existe
            role_exists = db.query(Roles).filter(Roles.id == role_id).first()
            if not role_exists:
                return None, {"role_id": "El rol especificado no existe"}

            # 1. Crear usuario
            user = User(
                email=email,
                full_name=full_name,
                password_hash=generate_password_hash(password),
                identification = identification
            )

            db.add(user)
            db.flush()  
            # flush escribe en DB SIN hacer commit esto genera el user.id

            # 2. Crear relación usuario-rol
            user_role = Users_roles(
                user_id=user.id,
                role_id=role_id
            )

            db.add(user_role)

            # 3. Commit final (todo o nada)
            db.commit()

            db.refresh(user)

            return user, None

        except IntegrityError as e:
            db.rollback()
            return None, {"db_error": str(e)}
     

