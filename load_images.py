import os
import cloudinary
import cloudinary.uploader

from db.db import SessionLocal
from db.models import Therapeutic_group

SVG_FOLDER = "images/unprocessed"

db = SessionLocal()

groups = db.query(Therapeutic_group).all()

for group in groups:

    file_path = os.path.join(
        SVG_FOLDER,
        f"{group.id}.svg"
    )

    if not os.path.exists(file_path):
        print(f"Missing: {file_path}")
        continue

    result = cloudinary.uploader.upload(
        file_path,

        folder="therapeutic_groups",

        public_id=str(group.id),

        overwrite=True,

        resource_type="image"
    )

    group.image_url = result["secure_url"]

    print(
        f"Uploaded therapeutic group {group.id}"
    )

db.commit()
db.close()