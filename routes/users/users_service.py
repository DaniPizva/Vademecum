

# routes\users\users_service.py
from typing import Any, Dict, List, Tuple, Optional
from flask import request
from contextlib import contextmanager
from db.db import SessionLocal
from db.models import User, UserRole
from sqlalchemy.orm import joinedload
import datetime
from datetime import timezone



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



def getAll() -> Tuple[List[User], Any]:
    with get_db() as db:
        users = (db.query(User)
                 .options(joinedload(User.roles)
                          .joinedload(UserRole.role))
                 .all())
        return users, None


def delete(id: int) -> Tuple[bool, Any]:
    with get_db() as db:
        user = db.query(User).filter(User.id == id).first()
        if not user:
            return False, {"id": "User not found"}
        user.is_active = False
        user.updated_at = datetime.now(timezone.utc)
        db.commit()
        return True, None


def update(id: int, data: Dict[str, Any]) -> Tuple[Optional[User], Any]:
    """Only profile fields; password change is forbidden here."""
    with get_db() as db:
        user = db.query(User).filter(User.id == id).first()
        if not user:
            return False, {"id": f"User with {id} not found"}
        
        # Update allowed fields (no password)
        if "full_name" in data:
            user.full_name = data["full_name"].strip()
        if "email" in data:
            user.email = data["email"].strip()
        
        if "is_active" in data:
            if isinstance(data["is_active"], bool):
                user.is_active = data["is_active"]
            else:
                return False, {"is_active": "Must be boolean (true/false)"}
            
            
        user.updated_at = datetime.now(timezone.utc)
        db.commit()
        db.refresh(user)
        return user, None

    