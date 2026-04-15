#es el unico que hace contacto con la base de datos, ni router ni controller hacen contacto

from typing import Any,Dict,List,Tuple, Optional
from flask import request
from contextlib import contextmanager
from db.db import SessionLocal

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
          t = db.query(User).all() 
          return t, None 





    