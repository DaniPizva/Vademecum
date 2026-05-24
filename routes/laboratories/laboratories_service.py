# routes\laboratories\laboratories_service.py

from typing import Any,Dict,List,Tuple, Optional
from flask import request
from contextlib import contextmanager
from db.db import SessionLocal
from db.models import Laboratory, Product
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
        try:
            cached = redis.get(cache_key)
            if cached:
                return json.loads(cached), None
        except Exception as e:
            pass


    with get_db() as db:
        labs = db.query(Laboratory).all()
        serialized = []
        for f in labs:
            # Compute product dependency count
            dep_count = db.query(Product)\
                          .filter(Product.laboratory_id == f.id)\
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
        lab = Laboratory(
            name=data['name'],
            logo_url=data.get('logo_url', ''),
            is_active=True
        )
        db.add(lab)
        db.commit()
        redis = get_redis()
        if redis:
            redis.delete("catalog:laboratories")
        return lab.to_dict(), None

def toggle_laboratory_state(id: int):
    with get_db() as db:
        lab = db.query(Laboratory).filter(Laboratory.id == id).first()
        if not lab:
            return False, {"id": "Laboratory not found"}

        lab.is_active = not lab.is_active
        db.commit()
        redis = get_redis()
        if redis:
            redis.delete("catalog:laboratories")
        return {"id": id, "is_active": lab.is_active}, None
    
    
def updateLaboratory(id: int,data: Dict[str, Any]) -> Tuple[Optional[Laboratory],Any]: #flecha es lo que devuelve
     with get_db() as db: #conecta db
          l = db.query(Laboratory).filter(Laboratory.id == id).first()
          if not l:
               return False, {"id": "Laboratory with:" + str(id) + "not found"} #para ser mas especifico
          l.name = (data.get("name") or "").strip()  #para que busque el name y que quite los espacios # toca agregas mas dependiendo de si la cLaboratory tiene mas cosas
          db.commit() #commit ---> lo mete a la db, y refresh manual
          db.refresh(l)
          return l, None