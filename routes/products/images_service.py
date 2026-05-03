from db.mongo import get_mongo_db

def get_main_image(owner_type: str, owner_id: int):
    db = get_mongo_db()

    image = db.images.find_one(
        {
            "owner_type": owner_type,
            "owner_id": owner_id,
            "image_type": "frontal"
        },
        {"_id": 0, "image_url": 1}
    )

    return image["image_url"] if image else None


def get_images_map(owner_type: str, owner_ids: list[int]):
    db = get_mongo_db()

    cursor = db.images.find(
        {
            "owner_type": owner_type,
            "owner_id": {"$in": owner_ids},
            "image_type": "frontal"
        },
        {"_id": 0, "owner_id": 1, "image_url": 1}
    )

    return {doc["owner_id"]: doc["image_url"] for doc in cursor}