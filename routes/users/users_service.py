# routes/users/users_service.py
from typing import Any, Dict, List, Tuple, Optional
from flask import current_app
from contextlib import contextmanager
from db.db import SessionLocal
from db.models import User, UserRole
from sqlalchemy.orm import joinedload
from sqlalchemy.exc import IntegrityError  # corrected import (was django)
from datetime import timezone, datetime
import json

# ------------------------------------------------------------------------------
# Redis client helper (same as auth_service)
# ------------------------------------------------------------------------------

def get_redis():
    """Return Redis client from Flask current_app."""
    return current_app.redis if hasattr(current_app, 'redis') else None

# ------------------------------------------------------------------------------
# Database session (unchanged)
# ------------------------------------------------------------------------------

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

# ------------------------------------------------------------------------------
# Cache helpers for user lists and details
# ------------------------------------------------------------------------------

def invalidate_user_lists():
    """Invalidate all admin user listing caches."""
    redis = get_redis()
    if redis:
        redis.delete("users:list")
        redis.delete("users:viewmodels")

def invalidate_user_detail(user_id: int):
    """Invalidate single user detail cache."""
    redis = get_redis()
    if redis:
        redis.delete(f"user:{user_id}")

def invalidate_user_session(user_id: int):
    """Invalidate session cache for a user (imported from auth_service pattern)."""
    redis = get_redis()
    if redis:
        redis.delete(f"user:session:{user_id}")

def invalidate_user_roles(user_id: int):
    """Invalidate RBAC roles cache."""
    redis = get_redis()
    if redis:
        redis.delete(f"user:roles:{user_id}")

def cache_user_list(users_dict: List[Dict], ttl_seconds: int = 300):
    """Store raw user list in Redis (users:list)."""
    redis = get_redis()
    if redis:
        redis.setex("users:list", ttl_seconds, json.dumps(users_dict))

def get_cached_user_list() -> Optional[List[Dict]]:
    """Retrieve cached raw user list."""
    redis = get_redis()
    if redis:
        data = redis.get("users:list")
        if data:
            return json.loads(data)
    return None

def cache_viewmodel_list(viewmodels: List[Dict], ttl_seconds: int = 300):
    """Store pre‑transformed user viewmodels."""
    redis = get_redis()
    if redis:
        redis.setex("users:viewmodels", ttl_seconds, json.dumps(viewmodels))

def get_cached_viewmodel_list() -> Optional[List[Dict]]:
    redis = get_redis()
    if redis:
        data = redis.get("users:viewmodels")
        if data:
            return json.loads(data)
    return None

def cache_single_user(user_id: int, user_dict: Dict, ttl_seconds: int = 900):
    """Cache individual user detail."""
    redis = get_redis()
    if redis:
        redis.setex(f"user:{user_id}", ttl_seconds, json.dumps(user_dict))

def get_cached_single_user(user_id: int) -> Optional[Dict]:
    redis = get_redis()
    if redis:
        data = redis.get(f"user:{user_id}")
        if data:
            return json.loads(data)
    return None

# ------------------------------------------------------------------------------
# Helper: Build flattened viewmodel (UI‑ready)
# ------------------------------------------------------------------------------

def build_user_viewmodel(user: User) -> Dict:
    """
    Transform a User ORM object into a UI‑ready viewmodel.
    Removes frontend mapping burden (role formatting, computed fields).
    """
    # Collect role names and codes
    role_names = []
    role_codes = []
    for ur in user.roles:
        if ur.role:
            role_names.append(ur.role.name)
            role_codes.append(ur.role.code)

    return {
        "id": user.id,
        "full_name": user.full_name,
        "email": user.email,
        "identification": user.identification,
        "is_active": user.is_active,
        "roles": [
            {"id": ur.role.id, "name": ur.role.name, "code": ur.role.code}
            for ur in user.roles if ur.role
        ],
        "role_names": ", ".join(role_names),      # UI ready
        "role_codes": role_codes,                 # for guards
        "created_at": user.created_at.isoformat() if user.created_at else None,
        "updated_at": user.updated_at.isoformat() if user.updated_at else None,
        "last_login_at": user.last_login_at.isoformat() if user.last_login_at else None,
        "first_login_at": user.first_login_at.isoformat() if user.first_login_at else None,
        "password_changed_at": user.password_changed_at.isoformat() if user.password_changed_at else None,
    }

# ------------------------------------------------------------------------------
# MAIN SERVICE FUNCTIONS (refactored with Redis)
# ------------------------------------------------------------------------------

def getAll() -> Tuple[List[Dict], Any]:
    """
    Get all users with roles – cache‑first (users:list).
    Returns serialized list of user dicts (not ORM objects).
    """
    # 1. Try Redis cache for raw user list
    cached = get_cached_user_list()
    if cached is not None:
        return cached, None

    # 2. Cache miss – query DB
    with get_db() as db:
        users = (db.query(User)
                 .options(joinedload(User.roles).joinedload(UserRole.role))
                 .all())

        # Serialize to dict inside session
        users_dict = [u.to_dict() for u in users]

        # 3. Store in Redis (TTL 5 minutes)
        cache_user_list(users_dict, ttl_seconds=300)

        return users_dict, None

def getAllViewModels() -> Tuple[List[Dict], Any]:
    """
    NEW endpoint support: returns pre‑transformed user viewmodels.
    Used by frontend to avoid mapping logic.
    """
    # 1. Try viewmodel cache
    cached = get_cached_viewmodel_list()
    if cached is not None:
        return cached, None

    # 2. Cache miss – build from DB
    with get_db() as db:
        users = (db.query(User)
                 .options(joinedload(User.roles).joinedload(UserRole.role))
                 .all())
        viewmodels = [build_user_viewmodel(u) for u in users]

        # 3. Cache and return
        cache_viewmodel_list(viewmodels, ttl_seconds=300)
        return viewmodels, None

def getById(id: int) -> Tuple[Optional[Dict], Any]:
    """
    Get single user by ID (u6_userdetail). Used by edit modals.
    Not originally present – added as cache‑first.
    """
    # 1. Try Redis
    cached = get_cached_single_user(id)
    if cached is not None:
        return cached, None

    # 2. Query DB
    with get_db() as db:
        user = (db.query(User)
                .options(joinedload(User.roles).joinedload(UserRole.role))
                .filter(User.id == id)
                .first())
        if not user:
            return None, {"id": f"User with id {id} not found"}

        user_dict = user.to_dict()
        # 3. Store in cache
        cache_single_user(id, user_dict, ttl_seconds=900)
        return user_dict, None

def delete(id: int) -> Tuple[bool, Any]:
    """Toggle user active status + invalidate all related caches."""
    with get_db() as db:
        user = db.query(User).filter(User.id == id).first()
        if not user:
            return False, {"id": "User not found"}

        # Toggle active status
        user.is_active = not user.is_active
        user.updated_at = datetime.now(timezone.utc)
        db.commit()

    # Invalidate caches after successful commit
    invalidate_user_lists()           # users:list, users:viewmodels
    invalidate_user_detail(id)        # user:{id}
    invalidate_user_session(id)       # user:session:{id}
    invalidate_user_roles(id)         # user:roles:{id}

    return True, None

def update(id: int, data: Dict[str, Any]) -> Tuple[Optional[Dict], Any]:
    """
    Update user fields (full_name, email) + invalidate caches.
    """
    with get_db() as db:
        db.expire_on_commit = False

        try:
            user = (db.query(User)
                    .options(joinedload(User.roles).joinedload(UserRole.role))
                    .filter(User.id == id)
                    .first())

            if not user:
                return None, {"id": f"User with {id} not found"}

            if not user.is_active:
                return None, {"id": f"User with {id} is deactivated"}

            # Update fields
            if "full_name" in data and data["full_name"]:
                user.full_name = data["full_name"].strip()
            if "email" in data and data["email"]:
                user.email = data["email"].strip()

            user.updated_at = datetime.now(timezone.utc)
            # Materialize roles to avoid detached instance issues
            user.roles = list(user.roles)

            db.commit()
            user_dict = user.to_dict()

            # After successful commit: invalidate caches
            invalidate_user_lists()           # users:list, users:viewmodels
            invalidate_user_detail(id)        # user:{id}
            invalidate_user_session(id)       # user:session:{id}
            # If role changes were possible, also invalidate roles cache
            invalidate_user_roles(id)

            # Optional: refresh single user cache immediately
            cache_single_user(id, user_dict, ttl_seconds=900)

            return user_dict, None

        except IntegrityError as e:
            db.rollback()
            return None, {"db_error": str(e)}
        except Exception as e:
            db.rollback()
            return None, {"error": str(e)}