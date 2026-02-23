#es el unico que hace contacto con la base de datos, ni router ni controller hacen contacto

from typing import Any,Dict,List,Tuple, Optional
from flask import request
from contextlib import contextmanager
from db.db import SessionLocal

from db.models import Therapeutic_group 

@contextmanager
def get_db():
        db = SessionLocal()
        try:
            yield db  #mientras que se consulte se mantenga en la operacion
        finally:
            db.close() #cuando se termine se cierra la sesion

def getAll()-> Tuple[List[Therapeutic_group], Any]:
    ## iniciar secion con la base de datos
     with get_db() as db: #  TRvez de la conexion con la db, re lo retorna al controller
          t = db.query(Therapeutic_group).all() #que consulte la tabla llamda city y que traiga todo
          return t, None #si tiene therapeutic_groupss y si no, que ninguno
     
def createTg(data: Dict[str, Any]) -> Tuple[Optional[Therapeutic_group],Any]: #flecha es lo que devuelve
     with get_db() as db: #conecta db
          t = Therapeutic_group(name=data['name']) #de data extraigo el nombre y lo pongo en ciudad
          db.add(t) #la agrega
          db.commit() #commit ---> lo mete a la db, y refresh manual
          db.refresh(t)
          return t, None

def deleteTg(id: int) -> Tuple[bool,Any]: #flecha es lo que devuelve
     with get_db() as db: #conecta db
          therapeutic_group_exist = db.query(Therapeutic_group).filter(Therapeutic_group.id == id).first() #devolver si existe la ciudad en cities exist
          if not therapeutic_group_exist:
               return False, {"id": "Therapeutic group not found"}
          db.delete(therapeutic_group_exist)# si existe entonces que borre la ciudad
          db.commit()
          return True,None

def updateTg(id: int,data: Dict[str, Any]) -> Tuple[Optional[Therapeutic_group],Any]: #flecha es lo que devuelve
     with get_db() as db: #conecta db
          t = db.query(Therapeutic_group).filter(Therapeutic_group.id == id).first()
          if not t:
               return False, {"id": "Therapeutic group with:" + str(id) + "not found"} #para ser mas especifico
          t.name = (data.get("name") or "").strip()  #para que busque el name y que quite los espacios # toca agregas mas dependiendo de si la categoria tiene mas cosas
          db.commit() #commit ---> lo mete a la db, y refresh manual
          db.refresh(t)
          return t, None




    