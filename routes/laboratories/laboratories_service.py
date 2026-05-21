# routes\laboratories\laboratories_service.py

from typing import Any,Dict,List,Tuple, Optional
from flask import request
from contextlib import contextmanager
from db.db import SessionLocal
from db.models import Laboratory
from flask import current_app
import json

def get_redis():
    return current_app.redis if hasattr(current_app, 'redis') else None

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

def getAll() -> Tuple[List[Dict], Any]:
    redis = get_redis()
    cache_key = "catalog:laboratories"
    
    if redis:
        cached = redis.get(cache_key)
        if cached:
            return json.loads(cached), None

    with get_db() as db:
        laboratories = db.query(Laboratory).all()
        serialized = [{"id": lab.id, "name": lab.name} for lab in laboratories]

    if redis:
        redis.setex(cache_key, 21600, json.dumps(serialized))

    return serialized, None
     
def createLaboratory(data: Dict[str, Any]) -> Tuple[Optional[Laboratory],Any]: #flecha es lo que devuelve
     with get_db() as db: #conecta db
          l = Laboratory(name=data['name']) #de data extraigo el nombre y lo pongo en ciudad
          db.add(l) #la agrega
          db.commit() #commit ---> lo mete a la db, y refresh manual
          db.refresh(l)
          
          
          redis = get_redis()
          if redis:
                    redis.delete("catalog:laboratories")
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