#es el unico que hace contacto con la base de datos, ni router ni controller hacen contacto
# routes\descriptions\descriptions_service.py
from typing import Any,Dict,List,Tuple, Optional
from flask import request
from contextlib import contextmanager
from db.db import SessionLocal
from flask import current_app
import json


from db.models import Description, Family, Product, Therapeutic_group

def get_redis():
    return current_app.redis if hasattr(current_app, 'redis') else None

def _invalidate_caches():
    redis = get_redis()
    if redis:
        redis.delete("catalog:descriptions")
        redis.delete("catalog:families")
        redis.delete("catalog:therapeutic_groups")

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
        try:
            cached = redis.get(cache_key)
            if cached:
                return json.loads(cached), None
        except Exception as e:
            pass

    with get_db() as db:
        descriptions = db.query(Description).all()
        serialized = []
        for d in descriptions:
            dep_count = db.query(Family)\
                          .filter(Family.description_id == d.id)\
                          .count()
            serialized.append({
                "id": d.id,
                "description": d.description,
                "is_active": d.is_active,
                "dependency_count": dep_count
            })

    if redis:
        try:
            redis.setex(cache_key, 21600, json.dumps(serialized))
        except Exception as e:
            print(f"[WARN] Redis SETEX failed: {e}")

    return serialized, None
     
def create(data: dict) -> Tuple[Any, Any]:
    therapeutic_group_id = data.get('therapeutic_group_id')
    if not therapeutic_group_id:
        return None, {"therapeutic_group_id": "Required"}

    with get_db() as db:
        tg = db.query(Therapeutic_group).filter(
            Therapeutic_group.id == therapeutic_group_id,
            Therapeutic_group.is_active == True
        ).first()
        if not tg:
            return None, {"therapeutic_group_id": "Therapeutic group does not exist or is inactive"}

        desc = Description(
            description=data['description'],
            therapeutic_group_id=therapeutic_group_id
        )
        db.add(desc)
        db.commit()

        redis = get_redis()
        if redis:
            redis.delete("catalog:descriptions")
            redis.delete("catalog:families")
            redis.delete("catalog:therapeutic_groups")

        return desc.to_dict(), None

def toggle_description_state(id: int):
    with get_db() as db:
        desc = db.query(Description).filter(Description.id == id).first()
        if not desc:
            return False, {"id": "Description not found"}

        if desc.is_active:
            desc.is_active = False
            db.commit()
            _invalidate_caches()
            return {"id": id, "is_active": False}, None

        # Activation: parent Therapeutic Group must be active
        if not desc.therapeutic_group_relation_d:
            return False, {"parent": "Description has no therapeutic group"}
        if not desc.therapeutic_group_relation_d.is_active:
            return False, {"parent": "Cannot activate description because its therapeutic group is inactive"}

        desc.is_active = True
        db.commit()
        _invalidate_caches()
        return {"id": id, "is_active": True}, None



def updateDescription(id: int,data: Dict[str, Any]) -> Tuple[Optional[Description],Any]: #flecha es lo que devuelve
     with get_db() as db: #conecta db
          d = db.query(Description).filter(Description.id == id).first()
          if not d:
               return False, {"id": "Description with:" + str(id) + "not found"} #para ser mas especifico
          d.description = (data.get("description") or "").strip()  #para que busque el name y que quite los espacios # toca agregas mas dependiendo de si la categoria tiene mas cosas
          db.commit() #commit ---> lo mete a la db, y refresh manual
          db.refresh(d)
          return d, None

