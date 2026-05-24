#es el unico que hace contacto con la base de datos, ni router ni controller hacen contacto

from typing import Any,Dict,List,Tuple, Optional
from flask import request
from contextlib import contextmanager
from db.db import SessionLocal
from flask import current_app
import json
from db.models import Therapeutic_group , Family, Description, Product

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

def getAll()-> Tuple[List[Therapeutic_group], Any]:
    redis = get_redis()
    cache_key = "catalog:therapeutic_groups"
    
    if redis:
        try:
            cached = redis.get(cache_key)
            if cached:
                return json.loads(cached), None
        except Exception as e:
            pass
          
    ## iniciar secion con la base de datos
    with get_db() as db: #  TRvez de la conexion con la db, re lo retorna al controller
          tgs = db.query(Therapeutic_group).all() #que consulte la tabla llamda city y que traiga todo
          serialized = []
          for tg in tgs:
               # Compute product dependency count
               dep_count = db.query(Product).join(Family).join(Description)\
                              .filter(Description.therapeutic_group_id == tg.id)\
                              .count()
               serialized.append({
                    "id": tg.id,
                    "name": tg.name,
                    "is_active": tg.is_active,        # include so frontend doesn’t need fallback
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
        tg = Therapeutic_group(
            name=data['name'],
            image_url=data.get('image_url', ''),
            is_active=True
        )
        db.add(tg)
        db.commit()
        redis = get_redis()
        if redis:
            redis.delete("catalog:therapeutic_groups")  # Use correct key
        return tg.to_dict(), None

def toggle_therapeutic_group_state(id: int):
    with get_db() as db:
        tg = db.query(Therapeutic_group).filter(Therapeutic_group.id == id).first()
        if not tg:
            return False, {"id": "Therapeutic group not found"}

        # No parent to validate
        tg.is_active = not tg.is_active
        db.commit()
        redis = get_redis()
        if redis:
            redis.delete("catalog:therapeutic_groups")
            redis.delete("catalog:descriptions")
            redis.delete("catalog:families")
        return {"id": id, "is_active": tg.is_active}, None

def updateTg(id: int,data: Dict[str, Any]) -> Tuple[Optional[Therapeutic_group],Any]: #flecha es lo que devuelve
     with get_db() as db: #conecta db
          tgs = db.query(Therapeutic_group).filter(Therapeutic_group.id == id).first()
          if not tgs:
               return False, {"id": "Therapeutic group with:" + str(id) + "not found"} #para ser mas especifico
          tgs.name = (data.get("name") or "").strip()  #para que busque el name y que quite los espacios # toca agregas mas dependiendo de si la categoria tiene mas cosas
          db.commit() #commit ---> lo mete a la db, y refresh manual
          db.refresh(tgs)
          return tgs, None




    