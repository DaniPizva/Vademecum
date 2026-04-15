from typing import Any,Dict,List,Tuple, Optional
from flask import request
from contextlib import contextmanager
from db.db import SessionLocal
from werkzeug.security import check_password_hash, generate_password_hash
from db.models import User, Users_roles

@contextmanager
def get_db():
        db = SessionLocal()
        try:
            yield db  #mientras que se consulte se mantenga en la operacion
        finally:
            db.close()

def loginUser(data): #flecha es lo que devuelve
    email = data.get("email" or "")
    password = data.get("password" or "")
    email = email.strip()
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
 
    if not email or not password:
        return None, {"email/password": "email y password son requeridos"}
 
    with get_db() as db:
        exists = db.query(User).filter(User.email == email).first()
        if exists:
            return None, {"email": "Ya existe un usuario con esa cédula"}
 
        user = User(
            email=email,
            full_name=full_name,
            password_hash=generate_password_hash(password)
        )
        db.add(user)
        db.commit()
        db.refresh(user)
        return user, None
     

