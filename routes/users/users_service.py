

# routes\users\users_service.py
from typing import Any, Dict, List, Tuple, Optional
from flask import request
from contextlib import contextmanager
from db.db import SessionLocal
from db.models import User, UserRole
from sqlalchemy.orm import joinedload
from datetime import timezone, datetime



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
        
        if user.is_active == False:
            user.is_active = True
        else:
            user.is_active = False
            
        user.updated_at = datetime.now(timezone.utc)
        db.commit()
        return True, None

def update(id: int, data: Dict[str, Any]) -> Tuple[Optional[User], Any]:
    with get_db() as db:
        db.expire_on_commit = False
        user = (
            db.query(User)
            .options(
                joinedload(User.roles)
                .joinedload(UserRole.role)       # ← load the whole chain
            )
            .filter(User.id == id)
            .first()
        )

        if not user:
            return False, {"id": f"User with {id} not found"}
        elif user.is_active == False:
            return False, {"id": f"user with {id} is deactivated."}

        if "full_name" in data:
            user.full_name = data["full_name"].strip()
        if "email" in data:
            user.email = data["email"].strip()

        user.updated_at = datetime.now(timezone.utc)
        db.commit()
        return user, None
    