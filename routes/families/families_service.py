# routes\families\families_service.py
from typing import Any, Dict, List, Tuple, Optional
from contextlib import contextmanager

from db.db import SessionLocal
from db.models import Family, Description, Product
from flask import current_app
import json


def get_redis():
    return current_app.redis if hasattr(current_app, 'redis') else None

def _invalidate_caches():
    redis = get_redis()
    if redis:
        redis.delete("catalog:families")
        redis.delete("catalog:descriptions")
        redis.delete("catalog:Therapeutic_groups")


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
        try:
            cached = redis.get(cache_key)
            if cached:
                return json.loads(cached), None
        except Exception as e:
            pass

    with get_db() as db:
        families = db.query(Family).all()
        serialized = []
        for f in families:
            # Compute product dependency count
            dep_count = db.query(Product)\
                          .filter(Product.family_id == f.id)\
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
    description_id = data.get('description_id')
    if not description_id:
        return None, {"description_id": "Required"}

    with get_db() as db:
        desc = db.query(Description).filter(
            Description.id == description_id,
            Description.is_active == True
        ).first()
        if not desc:
            return None, {"description_id": "Description does not exist or is inactive"}

        family = Family(
            name=data['name'],
            description_id=description_id,
            mechanism_of_action=data.get('mechanism_of_action', '')
        )
        db.add(family)
        db.commit()

        redis = get_redis()
        if redis:
            redis.delete("catalog:families")
            redis.delete("catalog:descriptions")
            redis.delete("catalog:therapeutic_groups")

        return family.to_dict(), None

def toggle_family_state(id: int):
    with get_db() as db:
        family = db.query(Family).filter(Family.id == id).first()
        if not family:
            return False, {"id": "Family not found"}

        if family.is_active:
            # Deactivation always allowed
            family.is_active = False
            db.commit()
            _invalidate_caches()
            return {"id": id, "is_active": False}, None

        # Activation: verify parent Description is active
        if not family.description_relation_f:
            return False, {"parent": "Family has no associated description"}
        if not family.description_relation_f.is_active:
            return False, {"parent": "Cannot activate family because its description is inactive"}

        family.is_active = True
        db.commit()
        _invalidate_caches()
        return {"id": id, "is_active": True}, None


        


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