# routes/auth/auth_service.py

from typing import Any, Dict, Tuple, Optional
from flask import request, current_app
from contextlib import contextmanager
from db.db import SessionLocal
from werkzeug.security import check_password_hash, generate_password_hash
from db.models import User, UserRole, Role, TermsVersion, UserTermsAcceptance, SecurityEvent, PasswordHistory
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import joinedload
import re
import secrets
import string
from datetime import datetime, timezone, timedelta
import random
import json
from routes.auth.email.service import send_new_user_email

# ------------------------------------------------------------------------------
# Redis client helper (singleton per Flask app context)
# ------------------------------------------------------------------------------

def get_redis():
    """Return Redis client from Flask current_app."""
    return current_app.redis

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
# Helper: email validation (unchanged)
# ------------------------------------------------------------------------------

def checkemail(email: str):
    pattern = (
        r'^[A-Za-z0-9._%+-]+'
        r'@[A-Za-z0-9.-]+'
        r'\.[A-Za-z]{2,}$'
    )
    if not re.match(pattern, email):
        raise ValueError('Invalid email format.')

def generate_temp_password(length=12):
    alphabet = string.ascii_letters + string.digits
    return ''.join(secrets.choice(alphabet) for _ in range(length))

# ------------------------------------------------------------------------------
# NEW: Session builder (removes duplication between loginUser and get_me)
# ------------------------------------------------------------------------------

def build_user_session(db, user: User) -> Dict[str, Any]:
    """
    Build the complete session payload from a User SQLAlchemy object.
    Uses the already-loaded user (with roles) and performs additional queries
    for terms if needed.
    """
    # --- Authorization (roles) ---
    roles_list = []
    for ur in user.roles:
        if ur.role:
            roles_list.append({
                "id": ur.role.id,
                "code": ur.role.code,
                "name": ur.role.name
            })

    # --- Credential state ---
    requires_password_change = user.password_changed_at is None
    first_login_completed = user.first_login_at is not None

    # --- Compliance (latest active terms) ---
    latest_terms = db.query(TermsVersion).filter(
        TermsVersion.is_active == True
    ).order_by(TermsVersion.effective_at.desc()).first()

    accepted_terms = None
    requires_terms_acceptance = False

    if latest_terms:
        acceptance = db.query(UserTermsAcceptance).filter(
            UserTermsAcceptance.user_id == user.id,
            UserTermsAcceptance.terms_version_id == latest_terms.id
        ).first()
        requires_terms_acceptance = acceptance is None
        if acceptance:
            accepted_terms = {
                "id": latest_terms.id,
                "version": latest_terms.version,
                "accepted_at": acceptance.accepted_at.isoformat()
            }

    # --- Access decision ---
    blocked_reasons = []
    if requires_password_change:
        blocked_reasons.append("PASSWORD_CHANGE_REQUIRED")
    if requires_terms_acceptance:
        blocked_reasons.append("TERMS_ACCEPTANCE_REQUIRED")
    can_enter = len(blocked_reasons) == 0

    session_payload = {
        "user": {
            "id": user.id,
            "full_name": user.full_name,
            "email": user.email,
            "is_active": user.is_active
        },
        "authorization": {
            "roles": roles_list
        },
        "compliance": {
            "requires_terms_acceptance": requires_terms_acceptance,
            "current_terms": {
                "id": latest_terms.id,
                "version": latest_terms.version,
                "effective_at": latest_terms.effective_at.isoformat()
            } if latest_terms else None,
            "accepted_terms": accepted_terms
        },
        "credential_state": {
            "requires_password_change": requires_password_change,
            "password_changed_at": user.password_changed_at.isoformat() if user.password_changed_at else None,
            "first_login_completed": first_login_completed
        },
        "access": {
            "can_enter_system": can_enter,
            "blocked_reason": "; ".join(blocked_reasons) if blocked_reasons else None
        }
    }
    return session_payload

# ------------------------------------------------------------------------------
# NEW: Redis cache helpers (session + roles + user lists)
# ------------------------------------------------------------------------------

def get_user_session_cache(user_id: int) -> Optional[Dict]:
    """Retrieve cached user session from Redis."""
    redis = get_redis()
    if not redis:
        return None
    key = f"user:session:{user_id}"
    data = redis.get(key)
    if data:
        return json.loads(data)
    return None

def set_user_session_cache(user_id: int, payload: Dict, ttl_seconds: int = 1800):
    """Store user session in Redis with TTL (default 30 minutes)."""
    redis = get_redis()
    if redis:
        key = f"user:session:{user_id}"
        redis.setex(key, ttl_seconds, json.dumps(payload))

def invalidate_user_session(user_id: int):
    """Delete session cache for a user."""
    redis = get_redis()
    if redis:
        redis.delete(f"user:session:{user_id}")

def get_user_roles_cache(user_id: int) -> Optional[list]:
    """Retrieve cached role list for a user."""
    redis = get_redis()
    if not redis:
        return None
    key = f"user:roles:{user_id}"
    data = redis.get(key)
    if data:
        return json.loads(data)
    return None

def set_user_roles_cache(user_id: int, roles: list, ttl_seconds: int = 21600):
    """Cache user roles (6 hours default)."""
    redis = get_redis()
    if redis:
        key = f"user:roles:{user_id}"
        redis.setex(key, ttl_seconds, json.dumps(roles))

def invalidate_user_roles(user_id: int):
    redis = get_redis()
    if redis:
        redis.delete(f"user:roles:{user_id}")

def invalidate_user_lists():
    """Invalidate global user listings (used after create/update/delete)."""
    redis = get_redis()
    if redis:
        redis.delete("users:list")
        redis.delete("users:viewmodels")

# ------------------------------------------------------------------------------
# ORIGINAL FUNCTIONS (REFACTORED WITH CACHE)
# ------------------------------------------------------------------------------

def loginUser(data):
    email = data.get("email", "").strip()
    password = data.get("password", "").strip()

    if not email or not password:
        return None, {"Credenciales": "Email y password son requeridas"}

    with get_db() as db:
        now = datetime.now(timezone.utc)
        user = db.query(User).options(
            joinedload(User.roles).joinedload(UserRole.role)
        ).filter(User.email == email).first()

        if not user:
            return None, {"message": "User not found"}
        if not user.is_active:
            return None, {"message": "User is NOT active"}
        if not check_password_hash(user.password_hash, password):
            return None, {"message": "Incorrect password, try again"}

        # Update last login (write side effect – still required)
        if user.first_login_at is None:
            user.first_login_at = now
        user.last_login_at = now
        db.commit()

        # Build session payload (one unified builder)
        session_payload = build_user_session(db, user)

        # Store in Redis cache
        set_user_session_cache(user.id, session_payload)

        # Also cache roles separately for RBAC middleware
        roles_list = [role["id"] for role in session_payload["authorization"]["roles"]]
        set_user_roles_cache(user.id, roles_list)

        return session_payload, None

def get_me(user_id: int) -> Tuple[Optional[Dict], Any]:
    # 1. Try Redis cache first
    cached = get_user_session_cache(user_id)
    if cached:
        return cached, None

    # 2. Cache miss – rebuild from DB
    with get_db() as db:
        user = db.query(User).options(
            joinedload(User.roles).joinedload(UserRole.role)
        ).filter(User.id == user_id).first()

        if not user:
            return None, {"message": "User not found"}

        session_payload = build_user_session(db, user)

        # Store in cache for future requests
        set_user_session_cache(user_id, session_payload)

        # Also cache roles
        roles_list = [role["id"] for role in session_payload["authorization"]["roles"]]
        set_user_roles_cache(user_id, roles_list)

        return session_payload, None

def createUser(data: Dict[str, Any]) -> Tuple[Optional[Dict], Any]:
    email = (data.get("email") or "").strip()
    full_name = (data.get("full_name") or "").strip()
    role_id = data.get("role_id")
    identification = data.get("identification")

    if not email or not full_name or not role_id or not identification:
        return None, {
            "error": "email, full_name, role_id y identification son requeridos"
        }

    checkemail(email)

    temp_password = generate_temp_password()
    now = datetime.now(timezone.utc)

    with get_db() as db:
        db.expire_on_commit = False

        try:
            existing_user = db.query(User).filter(User.email == email).first()
            if existing_user:
                return None, {"email": "Ya existe un usuario con ese correo"}

            role = db.query(Role).filter(Role.id == role_id).first()
            if not role:
                return None, {"role_id": "El rol especificado no existe"}

            verification_code = str(random.randint(10000, 99999))
            verification_expires = now + timedelta(minutes=15)

            user = User(
                email=email,
                full_name=full_name,
                identification=identification,
                password_hash=generate_password_hash(temp_password),
                is_active=True,
                created_at=now,
                updated_at=now,
                temporary_verification_code=verification_code,
                verification_code_expires_at=verification_expires
            )

            db.add(user)
            db.flush()

            user_role = UserRole(
                user_id=user.id,
                role_id=role_id,
                assigned_at=now,
                assigned_by=None
            )
            user_role.role = role
            db.add(user_role)
            user.roles = [user_role]
            db.commit()

            try:
                send_new_user_email(
                    to_email=user.email,
                    full_name=user.full_name,
                    temp_password=temp_password,
                    verification_code=verification_code
                )
            except Exception as email_error:
                print("EMAIL ERROR:", str(email_error))

            # Invalidate global user lists (admin panels)
            invalidate_user_lists()

            user_data = user.to_dict()
            return {"user": user_data, "temp_password": temp_password}, None

        except IntegrityError as e:
            db.rollback()
            return None, {"db_error": str(e)}
        except Exception as e:
            db.rollback()
            return None, {"error": str(e)}

def accept_terms(user_id: int, ip_address: str = None, user_agent: str = None) -> Tuple[bool, Any]:
    with get_db() as db:
        user = db.query(User).filter(User.id == user_id).first()
        if not user:
            return False, {"message": "User not found"}

        latest_terms = db.query(TermsVersion).filter(
            TermsVersion.is_active == True
        ).order_by(TermsVersion.effective_at.desc()).first()

        if not latest_terms:
            return False, {"message": "No active terms version found"}

        existing = db.query(UserTermsAcceptance).filter(
            UserTermsAcceptance.user_id == user_id,
            UserTermsAcceptance.terms_version_id == latest_terms.id
        ).first()
        if existing:
            return True, None  # idempotent

        acceptance = UserTermsAcceptance(
            user_id=user_id,
            terms_version_id=latest_terms.id,
            accepted_at=datetime.now(timezone.utc),
            ip_address=ip_address,
            user_agent=user_agent,
            acceptance_method="from API"
        )
        db.add(acceptance)
        db.commit()

    # After terms acceptance, the user's session state changes
    invalidate_user_session(user_id)
    return True, None

def change_password(user_id: int, data: Dict[str, Any]) -> Tuple[bool, Any]:
    new_password = (data.get("new_password") or "").strip()
    current_password = (data.get("current_password") or "").strip()

    if not new_password:
        return False, {"message": "new_password es requerido"}

    with get_db() as db:
        user = db.query(User).filter(User.id == user_id).first()
        if not user:
            return False, {"message": "User not found"}

        verification_code = (data.get("verification_code") or "").strip()

        if user.password_changed_at is None:
            if not verification_code:
                return False, {"message": "verification_code es requerido"}
            if (not user.temporary_verification_code or
                user.temporary_verification_code != verification_code):
                return False, {"message": "Código de verificación inválido"}
            if (user.verification_code_expires_at and
                datetime.now(timezone.utc) > user.verification_code_expires_at):
                return False, {"message": "Código expirado"}
        else:
            if not current_password:
                return False, {"message": "current_password es requerido"}
            if not check_password_hash(user.password_hash, current_password):
                return False, {"message": "Contraseña actual incorrecta"}

        user.password_hash = generate_password_hash(new_password)
        user.password_changed_at = datetime.now(timezone.utc)
        if user.first_login_at is None:
            user.first_login_at = datetime.now(timezone.utc)
        user.updated_at = datetime.now(timezone.utc)
        user.temporary_verification_code = None
        user.verification_code_expires_at = None
        db.add(PasswordHistory(user_id=user.id, password_hash=user.password_hash, created_at=datetime.now(timezone.utc)))
        db.commit()

    # After password change, invalidate session and user detail caches
    invalidate_user_session(user_id)
    # Also invalidate any user detail cache if used elsewhere
    redis = get_redis()
    if redis:
        redis.delete(f"user:{user_id}")

    return True, None