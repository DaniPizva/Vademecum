# routes/products/product_images_service.py
from typing import Tuple, Optional, Any
from db.db import SessionLocal
from db.models import Product, ProductImage
from routes.cloudinary import service as cloudinary_service

def upload_product_image(
    product_id: int,
    file_path: str,
    is_main: bool = False
) -> Tuple[Optional[ProductImage], Any]:
    """Upload image to Cloudinary and store URL in PostgreSQL."""
    db = SessionLocal()
    try:
        product = db.query(Product).filter(Product.id == product_id).first()
        if not product:
            return None, {"error": f"Product {product_id} not found"}

        image_url, error = cloudinary_service.upload_image(file_path, folder="vademecum")
        if error:
            return None, error

        if is_main:
            # Demote any existing main image
            db.query(ProductImage).filter(
                ProductImage.product_id == product_id,
                ProductImage.is_main == True
            ).update({"is_main": False})

        new_image = ProductImage(
            product_id=product_id,
            image_url=image_url,
            is_main=is_main
        )
        db.add(new_image)
        db.commit()
        db.refresh(new_image)
        return new_image, None
    except Exception as e:
        db.rollback()
        return None, {"error": str(e)}
    finally:
        db.close()

def delete_product_image(image_id: int) -> Tuple[bool, Any]:
    """Delete image record from PostgreSQL (Cloudinary file remains)."""
    db = SessionLocal()
    try:
        img = db.query(ProductImage).filter(ProductImage.id == image_id).first()
        if not img:
            return False, {"error": f"Image {image_id} not found"}
        db.delete(img)
        db.commit()
        return True, None
    except Exception as e:
        db.rollback()
        return False, {"error": str(e)}
    finally:
        db.close()

def set_main_image(product_id: int, image_id: int) -> Tuple[bool, Any]:
    """Set a specific image as the main image for the product."""
    db = SessionLocal()
    try:
        img = db.query(ProductImage).filter(
            ProductImage.id == image_id,
            ProductImage.product_id == product_id
        ).first()
        if not img:
            return False, {"error": "Image not found or does not belong to product"}

        # Demote current main
        db.query(ProductImage).filter(
            ProductImage.product_id == product_id,
            ProductImage.is_main == True
        ).update({"is_main": False})

        img.is_main = True
        db.commit()
        return True, None
    except Exception as e:
        db.rollback()
        return False, {"error": str(e)}
    finally:
        db.close()