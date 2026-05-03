# route : routes\cloudinary\service.py
import cloudinary.uploader
from common.cloudinary_config import cloudinary


def upload_image(file_path, folder="vademecum"):
    try:
        result = cloudinary.uploader.upload(
            file_path,
            folder=folder,
            transformation = [
                {"width": 500, "height": 500, "crop": "limit"},
                {"quality": "auto"}
                ]
        )
        return result["secure_url"], None
    
    except Exception as e:
        return None, {"cloudinary": str(e)}