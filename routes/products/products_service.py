# routes/products/products_service.py
from typing import Any, Dict, List, Tuple, Optional
from contextlib import contextmanager
from sqlalchemy.orm import joinedload
from db.db import SessionLocal
from db.models import Product, Family, Laboratory, Generic, Description, ProductImage
from flask import current_app
import json
from datetime import datetime, timezone



def get_redis():
    return current_app.redis if hasattr(current_app, 'redis') else None


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


def _serialize_product(product: Product) -> Dict:
    """Convert a fully loaded Product ORM object into a raw dict (without deep nested relations)."""
    return {
        "id": product.id,
        "commercial_name": product.commercial_name,
        "concentration": product.concentration,
        "dosage_form": product.dosage_form,
        "posology": product.posology,
        "notes": product.notes,
        "is_active": product.is_active,
        "family_id": product.family_id,
        "laboratory_id": product.laboratory_id,
        "generic_id": product.generic_id,
        "created_at": product.created_at.isoformat() if product.created_at else None,
        "updated_at": product.updated_at.isoformat() if product.updated_at else None,
        "image": product.main_image.image_url if product.main_image else None
    }

def _build_product_viewmodel(product: Product) -> Dict:
    """
    Build UI‑ready viewmodel for a fully loaded Product.
    Used for caching under `products:viewmodels` and `product:viewmodel:{id}`.
    """
    # Resolve family and therapeutic group
    family_name = None
    therapeutic_group = None
    if product.family_relation_p:
        family_name = product.family_relation_p.name
        if product.family_relation_p.description_relation_f:
            therapeutic_group = product.family_relation_p.description_relation_f.therapeutic_group_relation_d.name if product.family_relation_p.description_relation_f.therapeutic_group_relation_d else None

    laboratory_name = None
    if product.laboratory_relation_p:
        laboratory_name = product.laboratory_relation_p.name

    generic_name = None
    if product.generic_relation_p:
        generic_name = product.generic_relation_p.name

    return {
        "id": product.id,
        "title": product.commercial_name,
        "laboratory": laboratory_name,
        "therapeuticGroup": therapeutic_group,
        "dosageForm": product.dosage_form,
        "isActive": product.is_active,
        "imageUrl": product.main_image.image_url if product.main_image else None,
        "family": family_name,
        "generic": generic_name,
        "concentration": product.concentration,
        "posology": product.posology,
        "notes": product.notes
    }

# ------------------------------------------------------------------------------
# Cache helpers
# ------------------------------------------------------------------------------

def _invalidate_product_caches(product_id: int = None):
    """Invalidate all product‑related caches."""
    redis = get_redis()
    if not redis:
        return
    # Generic list caches
    redis.delete("products:list")
    redis.delete("products:viewmodels")
    # Grouping caches (future extension)
    for key in redis.scan_iter("products:group:*"):
        redis.delete(key)
    if product_id:
        redis.delete(f"product:{product_id}")
        redis.delete(f"product:viewmodel:{product_id}")


def getAll(include_family=True, include_laboratory=True, include_generic=True,
           include_description=True, include_therapeutic_group=True) -> Tuple[List[Dict], None]:
    redis = get_redis()
    if redis:
        cached = redis.get("products:list")
        if cached:
            return json.loads(cached), None

    with get_db() as db:
        products = db.query(Product).options(
            joinedload(Product.family_relation_p)
                .joinedload(Family.description_relation_f)
                .joinedload(Description.therapeutic_group_relation_d),
            joinedload(Product.laboratory_relation_p),
            joinedload(Product.generic_relation_p),
            joinedload(Product.images)
        ).all()

        serialized = [
            p.to_dict(
                include_family=include_family,
                include_laboratory=include_laboratory,
                include_generic=include_generic,
                include_description=include_description,
                include_therapeutic_group=include_therapeutic_group
            ) for p in products
        ]

    if redis:
        redis.setex("products:list", 300, json.dumps(serialized))
    return serialized, None

def getAllViewModels() -> Tuple[List[Dict], None]:
    """
    Get all products as UI‑ready viewmodels (for product catalog / admin grid).
    Cache key: products:viewmodels
    """
    redis = get_redis()
    if redis:
        cached = redis.get("products:viewmodels")
        if cached:
            return json.loads(cached), None

    with get_db() as db:
        products = db.query(Product).options(
            joinedload(Product.family_relation_p)
                .joinedload(Family.description_relation_f)
                .joinedload(Description.therapeutic_group_relation_d),
            joinedload(Product.laboratory_relation_p),
            joinedload(Product.generic_relation_p),
            joinedload(Product.images)
        ).all()

        viewmodels = [_build_product_viewmodel(p) for p in products]

    if redis:
        redis.setex("products:viewmodels", 600, json.dumps(viewmodels))  # TTL 10 min

    return viewmodels, None
def getById(id: int, include_family=True, include_laboratory=True, include_generic=True,
            include_description=True, include_therapeutic_group=True) -> Tuple[Optional[Dict], Any]:
    redis = get_redis()
    if redis:
        cached = redis.get(f"product:{id}")
        if cached:
            return json.loads(cached), None

    with get_db() as db:
        product = db.query(Product).options(
            joinedload(Product.family_relation_p)
                .joinedload(Family.description_relation_f)
                .joinedload(Description.therapeutic_group_relation_d),
            joinedload(Product.laboratory_relation_p),
            joinedload(Product.generic_relation_p),
            joinedload(Product.images)
        ).filter(Product.id == id).first()

        if not product:
            return None, {"id": f"Product with id {id} not found"}

        serialized = product.to_dict(
            include_family=include_family,
            include_laboratory=include_laboratory,
            include_generic=include_generic,
            include_description=include_description,
            include_therapeutic_group=include_therapeutic_group
        )

    if redis:
        redis.setex(f"product:{id}", 900, json.dumps(serialized))
    return serialized, None

def getViewById(id: int) -> Tuple[Optional[Dict], Any]:
    """
    Get a single product as UI‑ready viewmodel (for product detail page).
    Cache key: product:viewmodel:{id}
    """
    redis = get_redis()
    if redis:
        cached = redis.get(f"product:viewmodel:{id}")
        if cached:
            return json.loads(cached), None

    with get_db() as db:
        product = db.query(Product).options(
            joinedload(Product.family_relation_p)
                .joinedload(Family.description_relation_f)
                .joinedload(Description.therapeutic_group_relation_d),
            joinedload(Product.laboratory_relation_p),
            joinedload(Product.generic_relation_p),
            joinedload(Product.images)
        ).filter(Product.id == id).first()

        if not product:
            return None, {"id": f"Product with id {id} not found"}

        viewmodel = _build_product_viewmodel(product)

    if redis:
        redis.setex(f"product:viewmodel:{id}", 1800, json.dumps(viewmodel))  # TTL 30 min

    return viewmodel, None

def createProduct(data: Dict[str, Any]) -> Tuple[Optional[Product], Any]:
    """Create a new product (returns ORM object – not cached)."""
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
            lab_exist = db.query(Laboratory).filter(Laboratory.id == laboratory_id).first()
            if not lab_exist:
                return None, {"laboratory_id": "Laboratory not found"}

        generic_id = data.get("generic_id")
        if generic_id is not None:
            gen_exist = db.query(Generic).filter(Generic.id == generic_id).first()
            if not gen_exist:
                return None, {"generic_id": "Generic not found"}

        concentration = (data.get("concentration") or "").strip() or None
        dosage_form = (data.get("dosage_form") or "").strip() or None
        posology = (data.get("posology") or "").strip() or None
        notes = (data.get("notes") or "").strip() or None
        is_active = data.get("is_active", True)

        product = Product(
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
        db.add(product)
        db.commit()
        db.refresh(product)

        # Reload full relations (for controller's .to_dict())
        product = db.query(Product).options(
            joinedload(Product.family_relation_p)
                .joinedload(Family.description_relation_f)
                .joinedload(Description.therapeutic_group_relation_d),
            joinedload(Product.laboratory_relation_p),
            joinedload(Product.generic_relation_p),
            joinedload(Product.images)
        ).filter(Product.id == product.id).first()

    # Invalidate all product list caches (new product appears everywhere)
    _invalidate_product_caches()
    return product, None

def deleteProduct(id: int) -> Tuple[bool, Any]:
    """Toggle product active/inactive."""
    with get_db() as db:
        product = db.query(Product).filter(Product.id == id).first()
        if not product:
            return False, {"id": "Product not found"}
        product.is_active = not product.is_active
        db.commit()
        db.refresh(product)

    # Invalidate caches for this product and all lists
    _invalidate_product_caches(product_id=id)
    return True, None

def updateProduct(id: int, data: Dict[str, Any]) -> Tuple[Optional[Product], Any]:
    """Update product fields and return the updated ORM object."""
    with get_db() as db:
        product = db.query(Product).filter(Product.id == id).first()
        if not product:
            return None, {"id": "Product not found"}

        # Update fields (validation same as original)
        if "commercial_name" in data:
            name = (data.get("commercial_name") or "").strip()
            if not name:
                return None, {"commercial_name": "commercial_name cannot be empty"}
            product.commercial_name = name

        if "family_id" in data:
            family_id = data.get("family_id")
            family_exist = db.query(Family).filter(Family.id == family_id).first()
            if not family_exist:
                return None, {"family_id": "Family not found"}
            product.family_id = family_id

        if "laboratory_id" in data:
            lab_id = data.get("laboratory_id")
            if lab_id is not None:
                lab_exist = db.query(Laboratory).filter(Laboratory.id == lab_id).first()
                if not lab_exist:
                    return None, {"laboratory_id": "Laboratory not found"}
            product.laboratory_id = lab_id

        if "generic_id" in data:
            gen_id = data.get("generic_id")
            if gen_id is not None:
                gen_exist = db.query(Generic).filter(Generic.id == gen_id).first()
                if not gen_exist:
                    return None, {"generic_id": "Generic not found"}
            product.generic_id = gen_id

        if "concentration" in data:
            product.concentration = (data.get("concentration") or "").strip() or None
        if "dosage_form" in data:
            product.dosage_form = (data.get("dosage_form") or "").strip() or None
        if "posology" in data:
            product.posology = (data.get("posology") or "").strip() or None
        if "notes" in data:
            product.notes = (data.get("notes") or "").strip() or None
        if "is_active" in data:
            product.is_active = data.get("is_active")

        db.commit()
        db.refresh(product)

        # Reload full relations
        product = db.query(Product).options(
            joinedload(Product.family_relation_p)
                .joinedload(Family.description_relation_f)
                .joinedload(Description.therapeutic_group_relation_d),
            joinedload(Product.laboratory_relation_p),
            joinedload(Product.generic_relation_p),
            joinedload(Product.images)
        ).filter(Product.id == product.id).first()

    # Invalidate all caches (product data changed)
    _invalidate_product_caches(product_id=id)

    # Optional: pre‑warm raw and viewmodel caches for this product
    redis = get_redis()
    if redis:
        # Re‑store raw product dict
        raw_dict = _serialize_product(product)
        redis.setex(f"product:{id}", 900, json.dumps(raw_dict))
        # Re‑store viewmodel
        vm = _build_product_viewmodel(product)
        redis.setex(f"product:viewmodel:{id}", 1800, json.dumps(vm))

    return product, None