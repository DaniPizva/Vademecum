#es el unico que hace contacto con la base de datos, ni router ni controller hacen contacto

from typing import Any,Dict,List,Tuple, Optional
from flask import request
from contextlib import contextmanager
from db.db import SessionLocal

from db.models import Laboratory

@contextmanager
def get_db():

    db = SessionLocal()

    try:
        yield db

    except Exception:
        db.rollback()
        raise

    finally:
        db.close()

def getAll()-> Tuple[List[Laboratory], Any]:
    ## iniciar secion con la base de datos
     with get_db() as db: #  TRvez de la conexion con la db, re lo retorna al controller
          laboratories = db.query(Laboratory).all() #que consulte la tabla llamda Laboratory y que traiga todo
          return laboratories, None #si tiene Laboratories y si no, que ninguno
     
def createLaboratory(data: Dict[str, Any]) -> Tuple[Optional[Laboratory],Any]: #flecha es lo que devuelve
     with get_db() as db: #conecta db
          l = Laboratory(name=data['name']) #de data extraigo el nombre y lo pongo en ciudad
          db.add(l) #la agrega
          db.commit() #commit ---> lo mete a la db, y refresh manual
          db.refresh(l)
          return l, None

def deleteLaboratory(id: int) -> Tuple[bool,Any]: #flecha es lo que devuelve
     with get_db() as db: #conecta db
          laboratory_exist = db.query(Laboratory).filter(Laboratory.id == id).first() #devolver si existe la ciudad en Laboratories exist
          if not laboratory_exist:
               return False, {"id": "Laboratory not found"}
          db.delete(laboratory_exist)# si existe entonces que borre la ciudad
          db.commit()
          return True,None
     
def updateLaboratory(id: int,data: Dict[str, Any]) -> Tuple[Optional[Laboratory],Any]: #flecha es lo que devuelve
     with get_db() as db: #conecta db
          l = db.query(Laboratory).filter(Laboratory.id == id).first()
          if not l:
               return False, {"id": "Laboratory with:" + str(id) + "not found"} #para ser mas especifico
          l.name = (data.get("name") or "").strip()  #para que busque el name y que quite los espacios # toca agregas mas dependiendo de si la cLaboratory tiene mas cosas
          db.commit() #commit ---> lo mete a la db, y refresh manual
          db.refresh(l)
          return l, None