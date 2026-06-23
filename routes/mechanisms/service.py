# routes\mechanisms\service.py
from typing import Any, Dict, List, Tuple, Optional
from contextlib import contextmanager
from sqlalchemy.orm import joinedload
from db.db import SessionLocal
from db.models import Mechanisms,Family, Mechanisms, Product, Mechanisms, FamilyMechanisms
from flask import current_app
import json


def get_redis():
    return current_app.redis if hasattr(current_app, 'redis') else None

def _invalidate_caches():
    redis = get_redis()
    if redis:
        redis.delete("catalog:mechanisms")
        redis.delete("catalog:mechanisms")
        redis.delete("catalog:descriptions")


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
    cache_key = "catalog:mechanisms"

    if redis:
        try:
            cached = redis.get(cache_key)
            if cached:
                return json.loads(cached), None
        except Exception as e:
            pass

    with get_db() as db:
        mechanisms = (db.query(Mechanisms).options(joinedload(Mechanisms.families)).all())
        serialized = []
        for mechanism in mechanisms:
            # Compute product dependency count
            dependency_count = len(mechanism.families)
            serialized.append({
                "id": mechanism.id,
                "action": mechanism.action,
                "is_active": mechanism.is_active,
                "dependency_count": dependency_count
            })

    if redis:
        try:
            redis.setex(cache_key, 21600, json.dumps(serialized))
        except Exception:
            pass

    return serialized, None

def create(data):

    with get_db() as db:

        family = (
            db.query(Family)
            .filter(Family.id == data["family_id"])
            .first()
        )

        if not family:
            return None, {"family_id": "Family not found"}

        mechanism = Mechanisms(
            action=data.get("action", "").strip(),
            is_active=True
        )

        db.add(mechanism)

        family.mechanisms.append(mechanism)

        db.commit()

        db.refresh(mechanism)

        _invalidate_caches()

        return mechanism.to_dict(), None
    
def toggle_state(id: int):

    with get_db() as db:

        mechanism = (
            db.query(Mechanisms)
            .options(joinedload(Mechanisms.families))
            .filter(Mechanisms.id == id)
            .first()
        )

        if not mechanism:
            return False, {"id": "Mechanism not found"}

        # deactivate
        if mechanism.is_active:
            mechanism.is_active = False

            db.commit()

            _invalidate_caches()

            return {
                "id": mechanism.id,
                "is_active": False
            }, None

        # activate
        if not mechanism.families:
            return False, {
                "family": "Mechanism must be associated with at least one family"
            }

        mechanism.is_active = True

        db.commit()

        _invalidate_caches()

        return {
            "id": mechanism.id,
            "is_active": True
        }, None

def update(
    id: int,
    data: Dict[str, Any]
) -> Tuple[Optional[Mechanisms], Any]:

    with get_db() as db:

        mechanism = (
            db.query(Mechanisms)
            .options(joinedload(Mechanisms.families))
            .filter(Mechanisms.id == id)
            .first()
        )

        if not mechanism:
            return None, {"id": "Mechanism not found"}

        # --------------------------
        # Update mechanism action
        # --------------------------

        if "action" in data:

            action = (data.get("action") or "").strip()

            if not action:
                return None, {
                    "action": "Action cannot be empty"
                }

            mechanism.action = action

        # --------------------------
        # Update family associations
        # --------------------------

        if "family_ids" in data:

            family_ids = data.get("family_ids", [])

            if not isinstance(family_ids, list):
                return None, {
                    "family_ids": "Must be a list"
                }

            families = (
                db.query(Family)
                .filter(Family.id.in_(family_ids))
                .all()
            )

            if len(families) != len(set(family_ids)):
                return None, {
                    "family_ids": "One or more families do not exist"
                }

            mechanism.families = families

        db.commit()

        db.refresh(mechanism)

        _invalidate_caches()

        return mechanism.to_dict(), None