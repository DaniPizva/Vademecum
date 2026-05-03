class ProductImage:
    def __init__(self, **data):
        self._id = data.get("_id")
        self.product_id = data.get("product_id")
        self.name = data.get("name")
        self.image_data = data.get("image_data")  
        self.image_type = data.get("image_type")
        self.created_at = data.get("created_at")
        self.updated_at = data.get("updated_at")

    def to_dict(self):
        return {
            "id": str(self._id) if self._id else None,
            "product_id": self.product_id,
            "name": self.name,
            "image_data": self.image_data,          
            "image_type": self.image_type,
            "created_at": self.created_at,
            "updated_at": self.updated_at
        }

class DescriptionImage:
    def __init__(self, **data):
        self._id = data.get("_id")
        self.description_id = data.get("description_id")
        self.name = data.get("name")
        self.image_data = data.get("image_data")
        self.image_type = data.get("image_type")
        self.created_at = data.get("created_at")
        self.updated_at = data.get("updated_at")

    def to_dict(self):
        return {
            "id": str(self._id) if self._id else None,
            "description_id": self.description_id,   # fixed: was incorrectly "product_id"
            "name": self.name,
            "image_data": self.image_data,
            "image_type": self.image_type,
            "created_at": self.created_at,
            "updated_at": self.updated_at
        }

class UserImage:
    def __init__(self, **data):
        self._id = data.get("_id")
        self.user_id = data.get("user_id")
        self.name = data.get("name")
        self.image_data = data.get("image_data")
        self.image_type = data.get("image_type")
        self.created_at = data.get("created_at")
        self.updated_at = data.get("updated_at")

    def to_dict(self):
        return {
            "id": str(self._id) if self._id else None,
            "user_id": self.user_id,
            "name": self.name,
            "image_data": self.image_data,
            "image_type": self.image_type,
            "created_at": self.created_at,
            "updated_at": self.updated_at
        }