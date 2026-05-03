import os
from dotenv import load_dotenv
from db.mongo import get_mongo_db

load_dotenv()

def init_mongo():
    db = get_mongo_db()
    
    # Helper to create collection with validator
    def create_collection_if_not_exists(name, validator):
        if name not in db.list_collection_names():
            db.create_collection(name, validator=validator)
            print(f"Created collection: {name}")
        else:
            print(f"Collection already exists: {name}")
    
    # Validator for Products collection
    products_validator = {
        "$jsonSchema": {
            "bsonType": "object",
            "required": ["product_id", "name", "image_data", "image_type", "created_at", "updated_at"],
            "properties": {
                "_id": {"bsonType": "objectId"},
                "product_id": {"bsonType": "int", "minimum": 1},
                "name": {"bsonType": "string", "minLength": 1},
                "image_data": {"bsonType": "string", "maxLength": 15728640},  # ~15 MB base64
                "image_type": {"enum": ["frontal", "lateral", "etiqueta", "ingredientes", "otra"]},
                "created_at": {"bsonType": "date"},
                "updated_at": {"bsonType": "date"}
            },
            "additionalProperties": False
        }
    }
    
    # Validator for Description collection
    description_validator = {
        "$jsonSchema": {
            "bsonType": "object",
            "required": ["description_id", "name", "image_data", "image_type", "created_at", "updated_at"],
            "properties": {
                "_id": {"bsonType": "objectId"},
                "description_id": {"bsonType": "int", "minimum": 1},
                "name": {"bsonType": "string", "minLength": 1},
                "image_data": {"bsonType": "string", "maxLength": 15728640},
                "image_type": {"enum": ["frontal", "lateral", "etiqueta", "Composición", "otra"]},
                "created_at": {"bsonType": "date"},
                "updated_at": {"bsonType": "date"}
            },
            "additionalProperties": False
        }
    }
    
    # Validator for UserImages collection
    user_images_validator = {
        "$jsonSchema": {
            "bsonType": "object",
            "required": ["user_id", "name", "image_data", "image_type", "created_at", "updated_at"],
            "properties": {
                "_id": {"bsonType": "objectId"},
                "user_id": {"bsonType": "int", "minimum": 1},
                "name": {"bsonType": "string", "minLength": 1},
                "image_data": {"bsonType": "string", "maxLength": 15728640},
                "image_type": {"enum": ["profile", "ui_icon", "background", "design", "other"]},
                "created_at": {"bsonType": "date"},
                "updated_at": {"bsonType": "date"}
            },
            "additionalProperties": False
        }
    }
    
    # Create collections
    create_collection_if_not_exists(os.getenv("MONGO_COLLECTION_PRODUCTS"), products_validator)
    create_collection_if_not_exists(os.getenv("MONGO_COLLECTION_DESCRIPTION"), description_validator)
    create_collection_if_not_exists(os.getenv("MONGO_COLLECTION_USER_IMAGES"), user_images_validator)

if __name__ == "__main__":
    init_mongo()