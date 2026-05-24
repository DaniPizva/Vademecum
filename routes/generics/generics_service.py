#es el unico que hace contacto con la base de datos, ni router ni controller hacen contacto

from typing import Any,Dict,List,Tuple, Optional
from flask import request
from contextlib import contextmanager
from db.db import SessionLocal
from flask import current_app
import json

from db.models import Generic, Product

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
        try:
            cached = redis.get(cache_key)
            if cached:
                return json.loads(cached), None
        except Exception as e:
            pass

    with get_db() as db:
        generics = db.query(Generic).all()
        serialized = []
        for f in generics:
            # Compute product dependency count
            dep_count = db.query(Product)\
                          .filter(Product.generic_id == f.id)\
                          .count()
            serialized.append({
                "id": f.id,
                "name": f.name,
                "is_active": f.is_active,        # include so frontend doesn’t need fallback
                "dependency_count": dep_count
            })
            
    if redis:
        try:
            redis.setex(cache_key, 21600, json.dumps(serialized))
        except Exception:
            pass

    return serialized, None
     
def create(data: dict) -> Tuple[Any, Any]:
    with get_db() as db:
        gen = Generic(name=data['name'], is_active=True)
        db.add(gen)
        db.commit()
        redis = get_redis()
        if redis:
            redis.delete("catalog:generics")
        return gen.to_dict(), None

def toggle_generic_state(id: int):
    with get_db() as db:
        gen = db.query(Generic).filter(Generic.id == id).first()
        if not gen:
            return False, {"id": "Generic not found"}

        gen.is_active = not gen.is_active
        db.commit()
        redis = get_redis()
        if redis:
            redis.delete("catalog:generics")
        return {"id": id, "is_active": gen.is_active}, None
    
def updateGeneric(id: int,data: Dict[str, Any]) -> Tuple[Optional[Generic],Any]: #flecha es lo que devuelve
     with get_db() as db: #conecta db
          g = db.query(Generic).filter(Generic.id == id).first()
          if not g:
               return False, {"id": "Generic with:" + str(id) + "not found"} #para ser mas especifico
          g.name = (data.get("name") or "").strip()  #para que busque el name y que quite los espacios # toca agregas mas dependiendo de si la Generic tiene mas cosas
          db.commit() #commit ---> lo mete a la db, y refresh manual
          db.refresh(g)
          return g, None