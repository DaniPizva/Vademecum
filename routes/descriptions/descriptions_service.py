#es el unico que hace contacto con la base de datos, ni router ni controller hacen contacto

from typing import Any,Dict,List,Tuple, Optional
from flask import request
from contextlib import contextmanager
from db.db import SessionLocal
from flask import current_app
import json


from db.models import Description

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
    cache_key = "catalog:descriptions"
    
    if redis:
        cached = redis.get(cache_key)
        if cached:
            return json.loads(cached), None

    with get_db() as db:
        descriptions = db.query(Description).all()
        serialized = [{"id": d.id, "name": d.name} for d in descriptions]

    if redis:
        redis.setex(cache_key, 21600, json.dumps(serialized))

    return serialized, None
     
def createDescription(data: Dict[str, Any]) -> Tuple[Optional[Description],Any]: #flecha es lo que devuelve
     with get_db() as db: #conecta db
          d = Description(description=data['description'], therapeutic_group_id=data['therapeutic_group_id']) #de data extraigo el nombre y lo pongo en ciudad
          db.add(d) #la agrega
          db.commit() #commit ---> lo mete a la db, y refresh manual
          db.refresh(d)
          
          
          redis = get_redis()
          if redis:
               redis.delete("catalog:descriptions")
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

