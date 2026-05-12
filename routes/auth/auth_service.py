# routes\auth\auth_service.py

from typing import Any, Dict, Tuple, Optional
from flask import request
from contextlib import contextmanager
from db.db import SessionLocal
from werkzeug.security import check_password_hash, generate_password_hash
from db.models import User, UserRole, Role, TermsVersion, UserTermsAcceptance, SecurityEvent, PasswordHistory
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import joinedload
import re
import secrets
import string
from datetime import datetime, timezone

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
        
        
# Considerar borrarlo, el correo y su formato se chequea desde el forms de login.
def checkemail(email: str):
    pattern = r'^[A-Za-z0-9._%+-]+@(uces\.edu\.co|ces\.edu\.co)$'
    if not re.match(pattern, email):
        raise ValueError('Email must end with "uces.edu.co" or "ces.edu.co".')


def generate_temp_password(length=12):
    """Generate a secure random temporary password."""
    alphabet = string.ascii_letters + string.digits
    return ''.join(secrets.choice(alphabet) for _ in range(length))




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

        # Marcar primer acceso si corresponde
        if user.first_login_at is None:
            user.first_login_at = now
        user.last_login_at = now
        db.commit()

        # --- Authorization ---
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

        response = {
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
                "password_changed_at": user.password_changed_at.isoformat()
                    if user.password_changed_at else None,
                "first_login_completed": first_login_completed
            },
            "access": {
                "can_enter_system": can_enter,
                "blocked_reason": "; ".join(blocked_reasons) if blocked_reasons else None
            }
        }
        return response, None
def createUser(data: Dict[str, Any]) -> Tuple[Optional[Dict], Any]:
    email = (data.get("email") or "").strip()
    full_name = (data.get("full_name") or "").strip()
    role_id = data.get("role_id")
    identification = data.get("identification")

    if not email or not full_name or not role_id or not identification:
        return None, {"error": "email, full_name, role_id y identification son requeridos"}

    checkemail(email)

    temp_password = generate_temp_password()
    now = datetime.now(timezone.utc)

    with get_db() as db:
        # Prevent expiring on commit (keep all data in memory)
        db.expire_on_commit = False

        try:
            if db.query(User).filter(User.email == email).first():
                return None, {"email": "Ya existe un usuario con ese correo"}

            role = db.query(Role).filter(Role.id == role_id).first()
            if not role:
                return None, {"role_id": "El rol especificado no existe"}

            user = User(
                email=email,
                full_name=full_name,
                identification=identification,
                password_hash=generate_password_hash(temp_password),
                is_active=True,
                created_at=now,
                updated_at=now
            )
            db.add(user)
            db.flush()   # get user.id

            user_role = UserRole(
                user_id=user.id,
                role_id=role_id,
                assigned_at=now,
                assigned_by=None
            )
            db.add(user_role)

            # 🔁 Force the roles collection to be loaded
            user.roles = [user_role]          # ← replaces the empty InstrumentedList

            db.commit()
            # ❌ No db.refresh(user) – this would expire everything

            return {
                "user": user,
                "temp_password": temp_password
            }, None

        except IntegrityError as e:
            db.rollback()
            return None, {"db_error": str(e)}
        
def accept_terms(user_id: int,ip_address:str = None, user_agent:str =None) -> Tuple[bool, Any]:
    with get_db() as db:
        user = db.query(User).filter(User.id == user_id).first()
        if not user:
            return False, {"message": "User not found"}

        latest_terms = db.query(TermsVersion).filter(
            TermsVersion.is_active == True
        ).order_by(TermsVersion.effective_at.desc()).first()

        if not latest_terms:
            return False, {"message": "No active terms version found"}

        # Evitar duplicados
        existing = db.query(UserTermsAcceptance).filter(
            UserTermsAcceptance.user_id == user_id,
            UserTermsAcceptance.terms_version_id == latest_terms.id
        ).first()
        if existing:
            return True, None  # idempotente

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

        # Si el usuario nunca ha cambiado su password (aún usa la temporal)
        # no exigimos la contraseña actual.
        if user.password_changed_at is not None:
            if not current_password:
                return False, {"message": "current_password es requerido"}
            if not check_password_hash(user.password_hash, current_password):
                return False, {"message": "Contraseña actual incorrecta"}

        user.password_hash = generate_password_hash(new_password)
        user.password_changed_at = datetime.now(timezone.utc)
        user.updated_at = datetime.now(timezone.utc)
        db.add(PasswordHistory(user_id=user.id, password_hash=user.password_hash, created_at=datetime.now(timezone.utc)))
        db.commit()
        return True, None
    
    
def get_me(user_id: int) -> Tuple[Optional[Dict], Any]:

    with get_db() as db:

        user = db.query(User).options(
            joinedload(User.roles).joinedload(UserRole.role)
        ).filter(User.id == user_id).first()

        if not user:
            return None, {"message": "User not found"}

        # ------------------------------------------------------------------
        # Authorization
        # ------------------------------------------------------------------

        roles_list = []

        for ur in user.roles:

            if ur.role:

                roles_list.append({
                    "id": ur.role.id,
                    "code": ur.role.code,
                    "name": ur.role.name
                })

        # ------------------------------------------------------------------
        # Credential state
        # ------------------------------------------------------------------

        requires_password_change = user.password_changed_at is None

        first_login_completed = user.first_login_at is not None

        # ------------------------------------------------------------------
        # Compliance
        # ------------------------------------------------------------------

        latest_terms = db.query(TermsVersion).filter(
            TermsVersion.is_active == True
        ).order_by(
            TermsVersion.effective_at.desc()
        ).first()

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

        # ------------------------------------------------------------------
        # Access state
        # ------------------------------------------------------------------

        blocked_reasons = []

        if requires_password_change:
            blocked_reasons.append("PASSWORD_CHANGE_REQUIRED")

        if requires_terms_acceptance:
            blocked_reasons.append("TERMS_ACCEPTANCE_REQUIRED")

        can_enter = len(blocked_reasons) == 0

        return {

            "user": {
                "id": user.id,
                "email": user.email,
                "full_name": user.full_name,
                "is_active": user.is_active
            },

            "authorization": {
                "roles": roles_list
            },

            "compliance": {

                "requires_terms_acceptance":
                    requires_terms_acceptance,

                "current_terms": {

                    "id": latest_terms.id,
                    "version": latest_terms.version,
                    "effective_at":
                        latest_terms.effective_at.isoformat()

                } if latest_terms else None,

                "accepted_terms":
                    accepted_terms
            },

            "credential_state": {

                "requires_password_change":
                    requires_password_change,

                "password_changed_at":
                    user.password_changed_at.isoformat()
                    if user.password_changed_at
                    else None,

                "first_login_completed":
                    first_login_completed
            },

            "access": {

                "can_enter_system":
                    can_enter,

                "blocked_reason":
                    "; ".join(blocked_reasons)
                    if blocked_reasons
                    else None
            }

        }, None
        