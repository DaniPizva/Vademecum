#es el unico que hace contacto con la base de datos, ni router ni controller hacen contacto

from typing import Any,Dict,List,Tuple, Optional
from flask import request
from contextlib import contextmanager
from db.db import SessionLocal
from flask import current_app
import json

from db.models import Generic

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
    cache_key = "catalog:generics"
    
    if redis:
        cached = redis.get(cache_key)
        if cached:
            return json.loads(cached), None

    with get_db() as db:
        generics = db.query(Generic).all()
        serialized = [{"id": g.id, "name": g.name} for g in generics]

    if redis:
        redis.setex(cache_key, 21600, json.dumps(serialized))

    return serialized, None
     
def createGeneric(data: Dict[str, Any]) -> Tuple[Optional[Generic],Any]: #flecha es lo que devuelve
     with get_db() as db: #conecta db
          g = Generic(name=data['name']) #de data extraigo el nombre y lo pongo en ciudad
          db.add(g) #la agrega
          db.commit() #commit ---> lo mete a la db, y refresh manual
          db.refresh(g)
          
          
          redis = get_redis()
          if redis:
                    redis.delete("catalog:generics")
          return g, None

def deleteGeneric(id: int) -> Tuple[bool,Any]: #flecha es lo que devuelve
     with get_db() as db: #conecta db
          generic_exist = db.query(Generic).filter(Generic.id == id).first() #devolver si existe la ciudad en Generic exist
          if not generic_exist:
               return False, {"id": "generic not found"}
          db.delete(generic_exist)# si existe entonces que borre la ciudad
          db.commit()
          return True,None
     
def updateGeneric(id: int,data: Dict[str, Any]) -> Tuple[Optional[Generic],Any]: #flecha es lo que devuelve
     with get_db() as db: #conecta db
          g = db.query(Generic).filter(Generic.id == id).first()
          if not g:
               return False, {"id": "Generic with:" + str(id) + "not found"} #para ser mas especifico
          g.name = (data.get("name") or "").strip()  #para que busque el name y que quite los espacios # toca agregas mas dependiendo de si la Generic tiene mas cosas
          db.commit() #commit ---> lo mete a la db, y refresh manual
          db.refresh(g)
          return g, None