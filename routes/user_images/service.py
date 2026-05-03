# routes\products_images\products_images_service.py
from typing import Any, Dict, List, Tuple, Optional
from datetime import datetime
from bson import ObjectId
from pymongo.errors import PyMongoError
from contextlib import contextmanager
 
from db.mongo import get_mongo_db
from db.db import SessionLocal #para validar el product se tuvo que agregar
from db.mongo_models import ProductImage
from db.models import Product
import os
 
COLLECTION_NAME = os.getenv("MONGO_COLLECTION_PRODUCTS")
#en mongo elservice cambia:
#collection.find() [getall]
#collection.find_one()[create]
#collection.delete_one()[delete]
#collection.update_one()[update]

@contextmanager
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

def get_collection():
    db = get_mongo_db()
    return db[COLLECTION_NAME]
     
def get() -> Tuple[List[ProductImage], Any]:
    try:
        collection = get_collection()
        docs = collection.find()
        products_images = [ProductImage(**doc) for doc in docs]
        return products_images, None
    except PyMongoError as e:
        return [], {"mongo": str(e)}
 
def create(data: Dict[str, Any]) -> Tuple[Optional[ProductImage], Any]:
    try:
        now = datetime.utcnow()

        product_id = int(data["product_id"])

        # VALIDAR QUE EL PRODUCTO EXISTA
        with get_db() as db:
            product = db.query(Product).filter(Product.id == product_id).first()

            if not product:
                return None, {"product_id": "Product does not exist"}

        collection = get_collection()

        # VALIDAR QUE NO EXISTA YA UN DOCUMENTO CON EL MISMO "product_id"
        existing = collection.find_one({"product_id": product_id})
        if existing:
            return None, {"product_id": "An image for this product already exists"}

        doc = {
            "product_id": product_id,
            "name": (data.get("name") or "").strip(),
            "image_data": (data.get("image_url") or "").strip(),
            "image_type": (data.get("image_type") or "").strip(),
            "created_at": now,
            "updated_at": now
        }

        result = collection.insert_one(doc)

        saved = collection.find_one({"_id": result.inserted_id})
        return ProductImage(**saved), None

    except KeyError as e:
        return None, {"required": f"Missing field: {str(e)}"}
    except ValueError as e:
        return None, {"value": str(e)}
    except PyMongoError as e:
        return None, {"mongo": str(e)}
    
def delete(id: str) -> Tuple[bool, Any]:
    try:
        collection = get_collection()

        if not ObjectId.is_valid(id):
            return False, {"id": "Invalid ObjectId"}

        result = collection.delete_one({"_id": ObjectId(id)})

        if result.deleted_count == 0:
            return False, {"id": "Product Image not found"}

        return True, None

    except PyMongoError as e:
        return False, {"mongo": str(e)}

def update(id: str, data: Dict[str, Any]) -> Tuple[Optional[ProductImage], Any]:
    try:
        collection = get_collection()

        if not ObjectId.is_valid(id):
            return None, {"id": "Invalid ObjectId"}

        update_data = {
            "updated_at": datetime.utcnow()
        }

        if "name" in data:
            update_data["name"] = (data.get("name") or "").strip()

        if "image_data" in data:
            update_data["image_url"] = (data.get("image_data") or "").strip()

        if "image_type" in data:
            update_data["image_type"] = (data.get("image_type") or "").strip()

        if "product_id" in data:
            product_id = int(data.get("product_id"))

            # VALIDAR QUE EL PRODUCTO EXISTA
            with get_db() as db:
                product = db.query(Product).filter(Product.id == product_id).first()

                if not product:
                    return None, {"product_id": "Product does not exist"}

            update_data["product_id"] = product_id

        result = collection.update_one(
            {"_id": ObjectId(id)},
            {"$set": update_data}
        )

        if result.matched_count == 0:
            return None, {"id": f"Product Image with id {id} not found"}

        updated_doc = collection.find_one({"_id": ObjectId(id)})
        return ProductImage(**updated_doc), None

    except ValueError as e:
        return None, {"value": str(e)}
    except PyMongoError as e:
        return None, {"mongo": str(e)}
 