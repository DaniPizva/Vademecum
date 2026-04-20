# routes\products\products_service.py
from typing import Any, Dict, List, Tuple, Optional
from contextlib import contextmanager
from sqlalchemy.orm import joinedload
from db.db import SessionLocal
from db.models import Product, Family, Laboratory, Generic


@contextmanager
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def getAll() -> Tuple[List[Product], Any]:
    with get_db() as db:
        products = db.query(Product).options(
            joinedload(Product.family_relation_p),
            joinedload(Product.laboratory_relation_p),
            joinedload(Product.generic_relation_p),
        ).all()

        return products, None


def createProduct(data: Dict[str, Any]) -> Tuple[Optional[Product], Any]:
    with get_db() as db:

        commercial_name = (data.get("commercial_name") or "").strip()
        if not commercial_name:
            return None, {"commercial_name": "commercial_name is required"}

        family_id = data.get("family_id")
        if family_id is None:
            return None, {"family_id": "family_id is required"}

        family_exist = db.query(Family).filter(Family.id == family_id).first()
        if not family_exist:
            return None, {"family_id": "Family not found"}

        laboratory_id = data.get("laboratory_id")
        if laboratory_id is not None:
            laboratory_exist = db.query(Laboratory).filter(Laboratory.id == laboratory_id).first()
            if not laboratory_exist:
                return None, {"laboratory_id": "Laboratory not found"}

        generic_id = data.get("generic_id")
        if generic_id is not None:
            generic_exist = db.query(Generic).filter(Generic.id == generic_id).first()
            if not generic_exist:
                return None, {"generic_id": "Generic not found"}

        concentration = (data.get("concentration") or "").strip() or None
        dosage_form = (data.get("dosage_form") or "").strip() or None
        posology = (data.get("posology") or "").strip() or None
        notes = (data.get("notes") or "").strip() or None
        is_active = data.get("is_active", True)

        p = Product(
            family_id=family_id,
            laboratory_id=laboratory_id,
            generic_id=generic_id,
            commercial_name=commercial_name,
            concentration=concentration,
            dosage_form=dosage_form,
            posology=posology,
            notes=notes,
            is_active=is_active
        )

        db.add(p)
        db.commit()
        db.refresh(p)
        return p, None


def deleteProduct(id: int) -> Tuple[bool, Any]:
    with get_db() as db:
        product_exist = db.query(Product).filter(Product.id == id).first()
        if not product_exist:
            return False, {"id": "Product not found"}

        db.delete(product_exist)
        db.commit()
        return True, None


def updateProduct(id: int, data: Dict[str, Any]) -> Tuple[Optional[Product], Any]:
    with get_db() as db:
        p = db.query(Product).filter(Product.id == id).first()
        if not p:
            return None, {"id": "Product not found"}

        if "commercial_name" in data:
            commercial_name = (data.get("commercial_name") or "").strip()
            if not commercial_name:
                return None, {"commercial_name": "commercial_name cannot be empty"}
            p.commercial_name = commercial_name

        if "family_id" in data:
            family_id = data.get("family_id")
            family_exist = db.query(Family).filter(Family.id == family_id).first()
            if not family_exist:
                return None, {"family_id": "Family not found"}
            p.family_id = family_id

        if "laboratory_id" in data:
            laboratory_id = data.get("laboratory_id")
            if laboratory_id is not None:
                laboratory_exist = db.query(Laboratory).filter(Laboratory.id == laboratory_id).first()
                if not laboratory_exist:
                    return None, {"laboratory_id": "Laboratory not found"}
            p.laboratory_id = laboratory_id

        if "generic_id" in data:
            generic_id = data.get("generic_id")
            if generic_id is not None:
                generic_exist = db.query(Generic).filter(Generic.id == generic_id).first()
                if not generic_exist:
                    return None, {"generic_id": "Generic not found"}
            p.generic_id = generic_id

        if "concentration" in data:
            p.concentration = (data.get("concentration") or "").strip() or None

        if "dosage_form" in data:
            p.dosage_form = (data.get("dosage_form") or "").strip() or None

        if "posology" in data:
            p.posology = (data.get("posology") or "").strip() or None

        if "notes" in data:
            p.notes = (data.get("notes") or "").strip() or None

        if "is_active" in data:
            p.is_active = data.get("is_active")

        db.commit()
        db.refresh(p)
        return p, None