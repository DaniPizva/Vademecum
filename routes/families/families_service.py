from typing import Any, Dict, List, Tuple, Optional
from contextlib import contextmanager

from db.db import SessionLocal
from db.models import Family, Description
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
    cache_key = "catalog:families"
    
    if redis:
        cached = redis.get(cache_key)
        if cached:
            return json.loads(cached), None

    with get_db() as db:
        families = db.query(Family).all()
        serialized = [{"id": f.id, "name": f.name} for f in families]

    if redis:
        redis.setex(cache_key, 21600, json.dumps(serialized))

    return serialized, None


def createFamily(data: Dict[str, Any]) -> Tuple[Optional[Family], Any]:
    with get_db() as db:

        name = (data.get("name") or "").strip()
        if not name:
            return None, {"name": "name is required"}

        description_id = data.get("description_id")
        mechanism_of_action = (data.get("mechanism_of_action") or "").strip() or None

        if description_id is not None:
            description_exist = db.query(Description).filter(Description.id == description_id).first()
            if not description_exist:
                return None, {"description_id": "Description not found"}

        f = Family(
            name=name,
            description_id=description_id,
            mechanism_of_action=mechanism_of_action
        )

        db.add(f)
        db.commit()
        db.refresh(f)
        
        redis = get_redis()
        if redis:
               redis.delete("catalog:families")
        return f, None


def deleteFamily(id: int) -> Tuple[bool, Any]:
    with get_db() as db:
        family_exist = db.query(Family).filter(Family.id == id).first()
        if not family_exist:
            return False, {"id": "Family not found"}

        db.delete(family_exist)
        db.commit()
        return True, None


def updateFamily(id: int, data: Dict[str, Any]) -> Tuple[Optional[Family], Any]:
    with get_db() as db:
        f = db.query(Family).filter(Family.id == id).first()
        if not f:
            return None, {"id": "Family not found"}

        if "name" in data:
            name = (data.get("name") or "").strip()
            if not name:
                return None, {"name": "name cannot be empty"}
            f.name = name

        if "description_id" in data:
            description_id = data.get("description_id")

            if description_id is not None:
                description_exist = db.query(Description).filter(Description.id == description_id).first()
                if not description_exist:
                    return None, {"description_id": "Description not found"}

            f.description_id = description_id

        if "mechanism_of_action" in data:
            f.mechanism_of_action = (data.get("mechanism_of_action") or "").strip() or None

        db.commit()
        db.refresh(f)
        return f, None