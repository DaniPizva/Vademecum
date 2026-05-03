# route :  db\mongo_models.py
class Image:
    def __init__(self, **data):
        self._id = data.get("_id")
        self.owner_type = data.get("owner_type")   # product | description | user
        self.owner_id = data.get("owner_id")       # PostgreSQL ID
        self.image_url = data.get("image_url")
        self.image_type = data.get("image_type")
        self.created_at = data.get("created_at")
        self.updated_at = data.get("updated_at")

    def to_dict(self):
        return {
            "id": str(self._id) if self._id else None,
            "owner_type": self.owner_type,
            "owner_id": self.owner_id,
            "image_url": self.image_url,
            "image_type": self.image_type,
            "created_at": self.created_at,
            "updated_at": self.updated_at
        }