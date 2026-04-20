#es el unico que hace contacto con la base de datos, ni router ni controller hacen contacto

from typing import Any,Dict,List,Tuple, Optional
from flask import request
from contextlib import contextmanager
from db.db import SessionLocal
from werkzeug.security import generate_password_hash
from db.models import User

@contextmanager
def get_db():
        db = SessionLocal()
        try:
            yield db  #mientras que se consulte se mantenga en la operacion
        finally:
            db.close() #cuando se termine se cierra la sesion

def getAll()-> Tuple[List[User], Any]:
    ## iniciar secion con la base de datos
     with get_db() as db: 
          users = db.query(User).all() 
          return users, None 


def delete(id: int) -> Tuple[bool, Any]:
    with get_db() as db:
        users= db.query(User).filter(User.id == id).first()
        if not users:
            return False, {"id": "User not found"}
        
        #Inactivación
        users.is_active = 0
        
        
        db.commit()
        db.refresh(users)
        return True, None
    
def update(id: int,data: Dict[str, Any]) -> Tuple[Optional[User],Any]: #flecha es lo que devuelve
     with get_db() as db: #conecta db
          users = db.query(User).filter(User.id == id).first()
          if not users:
               return False, {"id": "User with:" + str(id) + "not found"} #para ser mas especifico
          users.full_name = (data.get("full_name") or "").strip()  #para que busque el name y que quite los espacios # toca agregas mas dependiendo de si la cUser tiene mas cosas
          users.password_hash = generate_password_hash(data.get("password"))
          db.commit() #commit ---> lo mete a la db, y refresh manual
          db.refresh(users)
          return users, None


    