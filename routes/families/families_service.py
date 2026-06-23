# routes\families\families_service.py
from typing import Any, Dict, List, Tuple, Optional
from contextlib import contextmanager
from sqlalchemy.orm import joinedload
from sqlalchemy import func

from db.db import SessionLocal
from db.models import Family, Description, Product, Mechanisms
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
        families = (db.query(Family).options(joinedload(Family.mechanisms)).all())
        serialized = []
        for f in families:
            # Compute product dependency count
            counts = (
                db.query(
                    Product.family_id,
                    func.count(Product.id)
                )
                .group_by(Product.family_id)
                .all()
            )

            count_map = dict(counts)
            dep_count = count_map.get(f.id, 0) 
                        
            serialized.append({
                "id": f.id,
                "name": f.name,
                "description_id": f.description_id,
                "mechanism_ids": [
                    m.id
                    for m in f.mechanisms
                ],
                "is_active": f.is_active,
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
            name=data["name"],
            description_id=description_id,
        )

        mechanism_ids = data.get("mechanism_ids", [])

        if mechanism_ids:

            mechanisms = (
                db.query(Mechanisms)
                .filter(Mechanisms.id.in_(mechanism_ids))
                .all()
            )

            if len(mechanisms) != len(set(mechanism_ids)):
                return None, {
                    "mechanism_ids": "One or more mechanisms do not exist"
                }

            family.mechanisms = mechanisms

        db.add(family)
        db.commit()
        db.refresh(family)

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

        # Activación -> verifica que su objeto a referenciar este activo
        if not family.description_relation_f:
            return False, {"parent": "Family has no associated description"}
        if not family.description_relation_f.is_active:
            return False, {"parent": "Cannot activate family because its description is inactive"}
        
        family.is_active = True
        db.commit()
        _invalidate_caches()
        return {"id": id, "is_active": True}, None


        


def updateFamily(
    id: int,
    data: Dict[str, Any]
):

    with get_db() as db:

        f = (
            db.query(Family)
            .options(joinedload(Family.mechanisms))
            .filter(Family.id == id)
            .first()
        )

        if not f:
            return None, {
                "id": "Family not found"
            }

        if "name" in data:

            name = (data.get("name") or "").strip()

            if not name:
                return None, {
                    "name": "name cannot be empty"
                }

            f.name = name

        if "description_id" in data:

            description_id = data.get("description_id")

            description = (
                db.query(Description)
                .filter(
                    Description.id == description_id
                )
                .first()
            )

            if not description:
                return None, {
                    "description_id":
                    "Description not found"
                }

            f.description_id = description_id

        if "mechanism_ids" in data:

            mechanism_ids = data.get(
                "mechanism_ids",
                []
            )

            mechanisms = (
                db.query(Mechanisms)
                .filter(
                    Mechanisms.id.in_(
                        mechanism_ids
                    )
                )
                .all()
            )

            if len(mechanisms) != len(set(mechanism_ids)):
                return None, {
                    "mechanism_ids":
                    "One or more mechanisms do not exist"
                }

            f.mechanisms = mechanisms

        db.commit()

        db.refresh(f)

        _invalidate_caches()

        return f.to_dict(), None