#es el unico que hace contacto con la base de datos, ni router ni controller hacen contacto

from typing import Any,Dict,List,Tuple, Optional
from flask import request
from contextlib import contextmanager
from db.db import SessionLocal

from db.models import Description

@contextmanager
def get_db():
        db = SessionLocal()
        try:
            yield db  #mientras que se consulte se mantenga en la operacion
        finally:
            db.close() #cuando se termine se cierra la sesion

def getAll()-> Tuple[List[Description], Any]:
    ## iniciar secion con la base de datos
     with get_db() as db: #  TRvez de la conexion con la db, re lo retorna al controller
          d = db.query(Description).all() #que consulte la tabla llamda city y que traiga todo
          return d, None #si tiene therapeutic_groupss y si no, que ninguno
     
def createDescription(data: Dict[str, Any]) -> Tuple[Optional[Description],Any]: #flecha es lo que devuelve
     with get_db() as db: #conecta db
          d = Description(description=data['description'], therapeutic_group_id=data['therapeutic_group_id']) #de data extraigo el nombre y lo pongo en ciudad
          db.add(d) #la agrega
          db.commit() #commit ---> lo mete a la db, y refresh manual
          db.refresh(d)
          return d, None

def deleteDescription(id: int) -> Tuple[bool,Any]: #flecha es lo que devuelve
     with get_db() as db: #conecta db
          descriptions_exist = db.query(Description).filter(Description.id == id).first() #devolver si existe la ciudad en cities exist
          if not descriptions_exist:
               return False, {"id": "Description not found"}
          db.delete(descriptions_exist)# si existe entonces que borre la ciudad
          db.commit()
          return True,None

def updateDescription(id: int,data: Dict[str, Any]) -> Tuple[Optional[Description],Any]: #flecha es lo que devuelve
     with get_db() as db: #conecta db
          d = db.query(Description).filter(Description.id == id).first()
          if not d:
               return False, {"id": "Description with:" + str(id) + "not found"} #para ser mas especifico
          d.description = (data.get("description") or "").strip()  #para que busque el name y que quite los espacios # toca agregas mas dependiendo de si la categoria tiene mas cosas
          db.commit() #commit ---> lo mete a la db, y refresh manual
          db.refresh(d)
          return d, None

