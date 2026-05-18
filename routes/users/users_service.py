# routes/users/users_service.py
from typing import Any, Dict, List, Tuple, Optional
from flask import current_app
from contextlib import contextmanager
from db.db import SessionLocal
from db.models import User, UserRole, UserImage
from sqlalchemy.orm import joinedload
from sqlalchemy.exc import IntegrityError  # corrected import (was django)
from datetime import timezone, datetime
from routes.cloudinary.service import upload_image, delete_image
import json
import os
import tempfile

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
        
        
# ------------------------------------------------------------------------------
# IMAGE HELPERS
# ------------------------------------------------------------------------------

def invalidate_user_image_caches(user_id: int):
    """
    Invalidate every cache affected by profile image changes.
    """

    invalidate_user_detail(user_id)
    invalidate_user_session(user_id)
    invalidate_user_lists()


# ------------------------------------------------------------------------------
# UPLOAD USER IMAGE
# ------------------------------------------------------------------------------

def upload_user_image(
    user_id: int,
    file_storage
) -> Tuple[Optional[Dict], Any]:

    """
    Upload user avatar to Cloudinary and persist DB record.

    Flow:
    1. Validate user
    2. Save temporary local file
    3. Upload to Cloudinary
    4. Remove previous image if exists
    5. Persist new UserImage record
    6. Invalidate caches
    """

    with get_db() as db:

        try:

            # ------------------------------------------------------------------
            # VALIDATE USER
            # ------------------------------------------------------------------

            user = (
                db.query(User)
                .filter(User.id == user_id)
                .first()
            )

            if not user:
                return None, {
                    "user": "User not found"
                }

            if not user.is_active:
                return None, {
                    "user": "User is deactivated"
                }

            # ------------------------------------------------------------------
            # VALIDATE FILE
            # ------------------------------------------------------------------

            if not file_storage:
                return None, {
                    "image": "No file provided"
                }

            if file_storage.filename == "":
                return None, {
                    "image": "Empty filename"
                }

            # ------------------------------------------------------------------
            # CREATE TEMP FILE
            # ------------------------------------------------------------------

            suffix = os.path.splitext(
                file_storage.filename
            )[1]

            temp_file = tempfile.NamedTemporaryFile(
                delete=False,
                suffix=suffix
            )

            temp_path = temp_file.name

            file_storage.save(temp_path)

            temp_file.close()

            # ------------------------------------------------------------------
            # UPLOAD TO CLOUDINARY
            # ------------------------------------------------------------------

            image_url, upload_error = upload_image(
                temp_path,
                folder="user_avatars"
            )

            # Remove local temp file immediately after upload
            if os.path.exists(temp_path):
                os.remove(temp_path)

            if upload_error:
                return None, upload_error

            # ------------------------------------------------------------------
            # REMOVE PREVIOUS IMAGE
            # ------------------------------------------------------------------

            existing_image = (
                db.query(UserImage)
                .filter(UserImage.user_id == user_id)
                .first()
            )

            if existing_image:

                # Delete old image from Cloudinary
                if existing_image.cloudinary_public_id:

                    delete_image(
                        existing_image.cloudinary_public_id
                    )

                # Remove DB record
                db.delete(existing_image)
                db.flush()

            # ------------------------------------------------------------------
            # EXTRACT CLOUDINARY PUBLIC ID
            # ------------------------------------------------------------------

            # Example:
            # https://res.cloudinary.com/demo/image/upload/v123/user_avatars/abc.jpg
            #
            # Needed:
            # user_avatars/abc

            public_id = None

            try:

                split_marker = "/upload/"

                if split_marker in image_url:

                    path_after_upload = image_url.split(
                        split_marker
                    )[1]

                    # remove version segment
                    path_parts = path_after_upload.split("/")

                    if path_parts[0].startswith("v"):
                        path_parts = path_parts[1:]

                    public_id = "/".join(path_parts)

                    # remove extension
                    public_id = os.path.splitext(
                        public_id
                    )[0]

            except Exception:
                public_id = None

            # ------------------------------------------------------------------
            # CREATE NEW IMAGE RECORD
            # ------------------------------------------------------------------

            new_image = UserImage(
                user_id=user_id,
                image_url=image_url,
                cloudinary_public_id=public_id
            )

            db.add(new_image)

            # ------------------------------------------------------------------
            # UPDATE USER TIMESTAMP
            # ------------------------------------------------------------------

            user.updated_at = datetime.now(timezone.utc)

            db.commit()

            # ------------------------------------------------------------------
            # INVALIDATE CACHES
            # ------------------------------------------------------------------

            invalidate_user_image_caches(user_id)

            # ------------------------------------------------------------------
            # RESPONSE
            # ------------------------------------------------------------------

            return {
                "profile_image_url": image_url
            }, None

        except Exception as e:

            db.rollback()

            return None, {
                "error": str(e)
            }


# ------------------------------------------------------------------------------
# DELETE USER IMAGE
# ------------------------------------------------------------------------------

def delete_user_image(
    user_id: int
) -> Tuple[bool, Any]:

    """
    Delete user's current avatar from:
    - Cloudinary
    - Database
    """

    with get_db() as db:

        try:

            # ------------------------------------------------------------------
            # VALIDATE USER
            # ------------------------------------------------------------------

            user = (
                db.query(User)
                .filter(User.id == user_id)
                .first()
            )

            if not user:
                return False, {
                    "user": "User not found"
                }

            # ------------------------------------------------------------------
            # FIND IMAGE RECORD
            # ------------------------------------------------------------------

            image_record = (
                db.query(UserImage)
                .filter(UserImage.user_id == user_id)
                .first()
            )

            if not image_record:
                return False, {
                    "image": "User has no profile image"
                }

            # ------------------------------------------------------------------
            # DELETE FROM CLOUDINARY
            # ------------------------------------------------------------------

            if image_record.cloudinary_public_id:

                delete_image(
                    image_record.cloudinary_public_id
                )

            # ------------------------------------------------------------------
            # DELETE DB RECORD
            # ------------------------------------------------------------------

            db.delete(image_record)

            user.updated_at = datetime.now(timezone.utc)

            db.commit()

            # ------------------------------------------------------------------
            # INVALIDATE CACHES
            # ------------------------------------------------------------------

            invalidate_user_image_caches(user_id)

            return True, None

        except Exception as e:

            db.rollback()

            return False, {
                "error": str(e)
            }