from typing import Any, Dict, List, Tuple, Optional
from datetime import datetime
from bson import ObjectId
from pymongo.errors import PyMongoError
from contextlib import contextmanager
 
from db.mongo import get_mongo_db
from db.db import SessionLocal #para validar el product se tuvo que agregar
from db.mongo_models import DescriptionImage
from db.models import Description
import os
 
COLLECTION_NAME = os.getenv("MONGO_COLLECTION_DESCRIPTION")
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
     
def getAll() -> Tuple[List[DescriptionImage], Any]:
    try:
        collection = get_collection()
        docs = collection.find()
        description_images = [DescriptionImage(**doc) for doc in docs]
        return description_images, None
    except PyMongoError as e:
        return [], {"mongo": str(e)}
 
def createDescriptionImage(data: Dict[str, Any]) -> Tuple[Optional[DescriptionImage], Any]:
    try:
        now = datetime.utcnow()

        description_id = int(data["description_id"])

        # VALIDAR QUE EL DESCRIPTTIONN EXISTA
        with get_db() as db:
            description = db.query(Description).filter(Description.id == description_id).first()
        
            if not description:
                return None, {"description_id": "Description does not exist"}
        
        collection = get_collection()

        #  VALIDAR QUE NO EXISTA YA UN DOCUMENTO CON EL MISMO "description_id".
        existing = collection.find_one({"description_id": description_id})
        if existing:
            return None, {"description_id": "An image for this description already exists"}

        doc = {
            "description_id": description_id,
            "name": (data.get("name") or "").strip(),
            "image_url": (data.get("image_url") or "").strip(),
            "image_type": (data.get("image_type") or "").strip(),
            "created_at": now,
            "updated_at": now
        }

        result = collection.insert_one(doc)

        saved = collection.find_one({"_id": result.inserted_id})
        return DescriptionImage(**saved), None

    except KeyError as e:
        return None, {"required": f"Missing field: {str(e)}"}
    except ValueError as e:
        return None, {"value": str(e)}
    except PyMongoError as e:
        return None, {"mongo": str(e)}
    
    
def deleteDescriptionImage(id: str) -> Tuple[bool, Any]:
    try:
        collection = get_collection()

        if not ObjectId.is_valid(id):
            return False, {"id": "Invalid ObjectId"}

        result = collection.delete_one({"_id": ObjectId(id)})

        if result.deleted_count == 0:
            return False, {"id": "Description Image not found"}

        return True, None

    except PyMongoError as e:
        return False, {"mongo": str(e)}

def updateDescriptionImage(id: str, data: Dict[str, Any]) -> Tuple[Optional[DescriptionImage], Any]:
    try:
        collection = get_collection()

        if not ObjectId.is_valid(id):
            return None, {"id": "Invalid ObjectId"}

        update_data = {
            "updated_at": datetime.utcnow()
        }

        if "name" in data:
            update_data["name"] = (data.get("name") or "").strip()

        if "image_url" in data:
            update_data["image_url"] = (data.get("image_url") or "").strip()

        if "image_type" in data:
            update_data["image_type"] = (data.get("image_type") or "").strip()

        if "description_id" in data:
            description_id = int(data.get("description_id"))

            # VALIDAR QUE EL DESCRIPTION EXISTA
            with get_db() as db:
                description = db.query(Description).filter(Description.id == description_id).first()

                if not description:
                    return None, {"description_id": "Description does not exist"}

            update_data["description_id"] = description_id

        result = collection.update_one(
            {"_id": ObjectId(id)},
            {"$set": update_data}
        )

        if result.matched_count == 0:
            return None, {"id": f"Description Image with id {id} not found"}

        updated_doc = collection.find_one({"_id": ObjectId(id)})
        return DescriptionImage(**updated_doc), None

    except ValueError as e:
        return None, {"value": str(e)}
    except PyMongoError as e:
        return None, {"mongo": str(e)}
 