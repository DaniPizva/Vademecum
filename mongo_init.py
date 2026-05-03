# route: mongo_init.py
import os
from dotenv import load_dotenv
from db.mongo import get_mongo_db

load_dotenv()

def init_mongo():
    db = get_mongo_db()

    collection_name = "images"

    if collection_name not in db.list_collection_names():
        db.create_collection(collection_name)
        print(f"Created collection: {collection_name}")
    else:
        print(f"Collection already exists: {collection_name}")
        db[collection_name].drop()

    # Schema validator (optional but recommended)
    validator = {
        "$jsonSchema": {
            "bsonType": "object",
            "required": ["owner_type", "owner_id", "image_url", "image_type"],
            "properties": {
                "_id": {"bsonType": "objectId"},
                "owner_type": {
                    "enum": ["product", "description", "user"]
                },
                "owner_id": {
                    "bsonType": "int",
                    "minimum": 1
                },
                "image_url": {
                    "bsonType": "string",
                    "minLength": 1
                },
                "image_type": {
                    "enum": ["frontal", "lateral", "etiqueta", "profile", "background", "other"]
                },
                "created_at": {"bsonType": "date"},
                "updated_at": {"bsonType": "date"}
            }
        }
    }

    db.command({
        "collMod": collection_name,
        "validator": validator,
        "validationLevel": "strict"
    })


    db[collection_name].create_index([
        ("owner_type", 1),
        ("owner_id", 1),
        ("image_type", 1)
    ])

    print("Indexes and validator ready")


if __name__ == "__main__":
    init_mongo()