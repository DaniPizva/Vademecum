# routes\PQRS\service.py

from typing import (
    Any,
    Dict,
    List,
    Tuple,
    Optional
)

from contextlib import contextmanager

from datetime import datetime

from flask import current_app

from sqlalchemy.orm import joinedload

from db.db import SessionLocal

from db.models import (
    Product,
    PQRSTicket,
    PQRSProductRelation,
    PQRSMessage
)

import json
import uuid


# =========================================================
# REDIS
# =========================================================

def get_redis():

    return (
        current_app.redis
        if hasattr(current_app, "redis")
        else None
    )


# =========================================================
# DATABASE SESSION
# =========================================================

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


# =========================================================
# PQRS CONFIGURATION
# =========================================================

PQRS_TYPES = [

    "Petición",

    "Queja",

    "Reclamo",

    "Sugerencia"
]


PQRS_CATEGORIES = [

    {
        "name": "Información Incorrecta",
        "requires_product": True
    },

    {
        "name": "Dosificación Incorrecta",
        "requires_product": True
    },

    {
        "name": "Producto Duplicado",
        "requires_product": True
    },

    {
        "name": "Imagen Incorrecta",
        "requires_product": True
    },

    {
        "name": "Error Farmacológico",
        "requires_product": True
    },

    {
        "name": "Problema Técnico",
        "requires_product": False
    },

    {
        "name": "Sugerencia",
        "requires_product": False
    },

    {
        "name": "Acceso al Sistema",
        "requires_product": False
    },

    {
        "name": "Otro",
        "requires_product": False
    }
]


VALID_STATUS = [

    "Pendiente",

    "En revisión",

    "Respondido",

    "Cerrado",

    "Archivado"
]


# =========================================================
# HELPERS
# =========================================================

def generate_ticket_code(
    ticket_id: int
) -> str:

    return f"PQRS-{ticket_id:04d}"

def generate_unique_ticket_code() -> str:
    date_part = datetime.utcnow().strftime("%Y%m%d")
    random_part = uuid.uuid4().hex[:6].upper()
    return f"PQRS-{date_part}-{random_part}"


def category_requires_product(
    category_name: str
) -> bool:

    for category in PQRS_CATEGORIES:

        if category["name"] == category_name:

            return category["requires_product"]

    return False


# =========================================================
# PUBLIC SERVICES
# =========================================================
def createPQRS(data: Dict[str, Any]) -> Tuple[Optional[PQRSTicket], Any]:
    with get_db() as db:
        # ---------- validation (unchanged) ----------
        required_fields = ["type", "category", "subject", "description", "priority", "user_name", "user_email"]
        errors = {}
        for field in required_fields:
            value = (data.get(field) or "").strip()
            if not value:
                errors[field] = f"{field} is required"
        if errors:
            return None, errors

        if data["type"] not in PQRS_TYPES:
            return None, {"type": "Invalid PQRS type"}

        category_names = [c["name"] for c in PQRS_CATEGORIES]
        if data["category"] not in category_names:
            return None, {"category": "Invalid PQRS category"}

        # ---------- product validation (if needed) ----------
        product = None
        requires_product = category_requires_product(data["category"])
        if requires_product:
            sku_code = (data.get("sku_code") or "").strip()
            if not sku_code:
                return None, {"sku_code": "SKU code required for this category"}
            product = db.query(Product).filter(Product.sku_code == sku_code).first()
            if not product:
                return None, {"sku_code": "Product with SKU not found"}

       # ---------- CREATE TICKET WITH TICKET CODE ----------
        ticket_code = generate_unique_ticket_code()  # use the helper from before
        ticket = PQRSTicket(
            ticket_code=ticket_code,
            type=data["type"],
            category=data["category"],
            subject=data["subject"],
            description=data["description"],
            priority=data["priority"],
            status="Pendiente",
            user_name=data["user_name"],
            user_email=data["user_email"]
        )

        db.add(ticket)
        db.commit()
        db.refresh(ticket)   # ticket.id is now available

        # ---------- CREATE PRODUCT RELATION (if any) ----------
        if product:
            relation = PQRSProductRelation(
                pqrs_id=ticket.id,
                product_id=product.id,
                issue_type=data["category"],
                product_snapshot_name=product.commercial_name,
                product_snapshot_sku=product.sku_code
            )
            db.add(relation)
            db.commit()

        # ---------- EAGER LOAD THE RELATIONSHIP BEFORE RETURNING ----------
        # Re-query the ticket with joinedload to make product_relations available
        # even after the session is closed.
        from sqlalchemy.orm import joinedload

        final_ticket = (
            db.query(PQRSTicket)
            .options(joinedload(PQRSTicket.product_relations))
            .filter(PQRSTicket.id == ticket.id)
            .first()
        )

        return final_ticket, None


def getTicket(
    ticket_code: str
) -> Tuple[Optional[PQRSTicket], Any]:

    with get_db() as db:

        ticket = (

            db.query(PQRSTicket)

            .options(
                joinedload(
                    PQRSTicket.product_relations
                ).joinedload(
                    PQRSProductRelation.product
                ),
                joinedload(
                    PQRSTicket.messages
                )
            )

            .filter(
                PQRSTicket.ticket_code == ticket_code
            )

            .first()
        )

        if not ticket:

            return None, {
                "ticket_code":
                "PQRS ticket not found"
            }

        return ticket, None
    
def respondPQRS(
    id: int,
    data: Dict[str, Any]
):

    with get_db() as db:

        ticket = (

            db.query(PQRSTicket)

            .options(
                joinedload(
                    PQRSTicket.messages
                )
            )

            .filter(
                PQRSTicket.id == id
            )

            .first()
        )

        if not ticket:

            return None, {
                "id":
                "PQRS ticket not found"
            }

        response_message = (
            data.get("response")
            or ""
        ).strip()

        if not response_message:

            return None, {
                "response":
                "Response message is required"
            }

        # =================================================
        # CREATE MESSAGE
        # =================================================

        message = PQRSMessage(

            pqrs_id=ticket.id,

            sender_type="admin",

            message=response_message
        )

        db.add(message)

        # =================================================
        # UPDATE TICKET STATUS
        # =================================================

        ticket.status = "Respondido"

        ticket.updated_at = (
            datetime.utcnow()
        )

        db.commit()

        db.refresh(ticket)

        return {

            "ticket_id":
                ticket.id,

            "ticket_code":
                ticket.ticket_code,

            "status":
                ticket.status,

            "message":
                message.to_dict()
        }, None


def validateSKU(
    sku_code: str
) -> Tuple[Optional[Dict], Any]:

    with get_db() as db:

        product = (

            db.query(Product)

            .options(
                joinedload(
                    Product.laboratory_relation_p
                )
            )

            .filter(
                Product.sku_code == sku_code
            )

            .first()
        )

        if not product:

            return None, {
                "sku_code":
                "Invalid SKU code"
            }

        response = {

            "valid": True,

            "product": {

                "id": product.id,

                "sku_code": product.sku_code,

                "commercial_name":
                    product.commercial_name,

                "concentration":
                    product.concentration,

                "laboratory":
                    (
                        product
                        .laboratory_relation_p
                        .name
                    )

                    if product.laboratory_relation_p

                    else None
            }
        }

        return response, None


def getCategories():

    return PQRS_CATEGORIES, None


def getTypes():

    return PQRS_TYPES, None


# =========================================================
# ADMIN SERVICES
# =========================================================

def getAllPQRS():

    with get_db() as db:

        tickets = (

            db.query(PQRSTicket)

            .options(
                joinedload(
                    PQRSTicket.product_relations
                ),
                joinedload(
                    PQRSTicket.messages
                )
            )

            .filter(
                PQRSTicket.status != "Archivado"
            )

            .order_by(
                PQRSTicket.created_at.desc()
            )

            .all()
        )

        serialized = [

            ticket.to_dict(
                include_products=True
            )

            for ticket in tickets
        ]

        return serialized, None


def getPQRSByStatus(
    status: str
):

    with get_db() as db:

        if status not in VALID_STATUS:

            return None, {
                "status":
                "Invalid status"
            }

        tickets = (

            db.query(PQRSTicket)

            .options(
                joinedload(
                    PQRSTicket.product_relations
                ),
                joinedload(
                    PQRSTicket.messages
                )
            )

            .filter(
                PQRSTicket.status == status
            )

            .order_by(
                PQRSTicket.created_at.desc()
            )

            .all()
        )

        serialized = [

            ticket.to_dict(
                include_products=True
            )

            for ticket in tickets
        ]

        return serialized, None


def updatePQRSStatus(
    id: int,
    data: Dict[str, Any]
):

    with get_db() as db:

        ticket = (

            db.query(PQRSTicket)

            .filter(
                PQRSTicket.id == id
            )

            .first()
        )

        if not ticket:

            return None, {
                "id":
                "PQRS ticket not found"
            }

        new_status = (
            data.get("status")
            or ""
        ).strip()

        if not new_status:

            return None, {
                "status":
                "Status is required"
            }

        if new_status not in VALID_STATUS:

            return None, {
                "status":
                "Invalid status"
            }

        ticket.status = new_status

        ticket.updated_at = (
            datetime.utcnow()
        )

        db.commit()

        db.refresh(ticket)

        return ticket, None


def respondPQRS(
    id: int,
    data: Dict[str, Any]
):

    with get_db() as db:

        ticket = (

            db.query(PQRSTicket)

            .filter(
                PQRSTicket.id == id
            )

            .first()
        )

        if not ticket:

            return None, {
                "id":
                "PQRS ticket not found"
            }

        response_message = (
            data.get("response")
            or ""
        ).strip()

        if not response_message:

            return None, {
                "response":
                "Response message is required"
            }

        # =============================================
        # TEMPORARY RESPONSE SYSTEM
        # =============================================
        # FUTURE:
        # CREATE PQRSMessage TABLE
        # =============================================

        ticket.status = "Respondido"

        ticket.updated_at = (
            datetime.utcnow()
        )

        db.commit()

        response_payload = {

            "ticket_code":
                ticket.ticket_code,

            "response":
                response_message,

            "status":
                ticket.status
        }

        return response_payload, None


def deletePQRS(
    id: int
):

    with get_db() as db:

        ticket = (

            db.query(PQRSTicket)

            .filter(
                PQRSTicket.id == id
            )

            .first()
        )

        if not ticket:

            return None, {
                "id":
                "PQRS ticket not found"
            }

        # =============================================
        # SOFT DELETE
        # =============================================

        ticket.status = "Archivado"

        ticket.updated_at = (
            datetime.utcnow()
        )

        db.commit()

        return True, None