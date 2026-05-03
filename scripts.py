#!/usr/bin/env python3
"""
Deterministic, idempotent bulk image ingestion pipeline.
Scans a folder of WebP images named <product_id>.webp,
uploads each to Cloudinary (public_id: products/<product_id>),
and upserts metadata into MongoDB respecting the schema validator.

Usage:
    python ingest_images.py [--dry-run] [--root FOLDER]

Environment variables (see .env) override defaults.
"""

import os
import sys
import time
import logging
from pathlib import Path
from datetime import datetime, timezone
from typing import Optional

import dotenv
import cloudinary
import cloudinary.uploader
from pymongo import MongoClient
from pymongo.errors import PyMongoError
from tqdm import tqdm

# ----------------------------------------------------------------------
# Configuration from environment
# ----------------------------------------------------------------------
dotenv.load_dotenv()

CLOUDINARY_CLOUD_NAME = os.getenv("CLOUDINARY_CLOUD_NAME")
CLOUDINARY_API_KEY = os.getenv("CLOUDINARY_API_KEY")
CLOUDINARY_API_SECRET = os.getenv("CLOUDINARY_API_SECRET")

MONGO_URI = os.getenv("MONGO_URI")
MONGO_DB = os.getenv("MONGO_DB_NAME")
MONGO_COLLECTION = os.getenv("MONGO_COLLECTION", "images")

IMAGES_ROOT = os.getenv("IMAGES_ROOT", "imagenes(de verdad)/products")
DRY_RUN = os.getenv("DRY_RUN", "false").lower() == "true"
OVERWRITE_CLOUDINARY = os.getenv("OVERWRITE_CLOUDINARY", "true").lower() == "true"

# Image type for product images (must match enum in validator)
IMAGE_TYPE = os.getenv("IMAGE_TYPE", "frontal")   # frontal, lateral, etiqueta, profile, background, other

# Optional: max retries for Cloudinary upload
UPLOAD_RETRIES = 2
RETRY_DELAY = 1  # seconds

# ----------------------------------------------------------------------
# Logging setup
# ----------------------------------------------------------------------
logging.basicConfig(
    level=logging.INFO,
    format="[%(levelname)s] %(message)s",
    handlers=[logging.StreamHandler(sys.stdout)]
)
logger = logging.getLogger("ingestion")

# ----------------------------------------------------------------------
# Cloudinary initialization
# ----------------------------------------------------------------------
def init_cloudinary():
    if not all([CLOUDINARY_CLOUD_NAME, CLOUDINARY_API_KEY, CLOUDINARY_API_SECRET]):
        logger.error("Missing Cloudinary credentials in environment")
        sys.exit(1)
    cloudinary.config(
        cloud_name=CLOUDINARY_CLOUD_NAME,
        api_key=CLOUDINARY_API_KEY,
        api_secret=CLOUDINARY_API_SECRET,
        secure=True
    )
    logger.info("Cloudinary configured")

# ----------------------------------------------------------------------
# MongoDB connection
# ----------------------------------------------------------------------
def get_mongo_collection():
    try:
        client = MongoClient(MONGO_URI)
        db = client[MONGO_DB]
        collection = db[MONGO_COLLECTION]
        # Ensure index for upsert efficiency (not strictly required by validator)
        collection.create_index([("owner_type", 1), ("owner_id", 1)], unique=True)
        return collection
    except PyMongoError as e:
        logger.error(f"MongoDB connection failed: {e}")
        sys.exit(1)

# ----------------------------------------------------------------------
# Validation
# ----------------------------------------------------------------------
def validate_filename(file_path: Path) -> Optional[int]:
    """Return product_id if filename is numeric.webp, else None."""
    if file_path.suffix.lower() != ".webp":
        logger.warning(f"Skipping non-WebP file: {file_path.name}")
        return None
    stem = file_path.stem
    try:
        product_id = int(stem)
        if product_id > 0:
            return product_id
        else:
            logger.warning(f"Invalid filename (non-positive): {file_path.name}")
            return None
    except ValueError:
        logger.warning(f"Invalid filename (not an integer): {file_path.name}")
        return None

# ----------------------------------------------------------------------
# Cloudinary upload with retry
# ----------------------------------------------------------------------
def upload_to_cloudinary(product_id: int, file_path: Path, dry_run: bool) -> Optional[str]:
    """Upload image to Cloudinary. Returns secure_url or None."""
    if dry_run:
        logger.info(f"[DRY RUN] Would upload {file_path.name} -> products/{product_id}")
        return "https://dry-run.example.com/" + str(product_id)

    public_id = f"products/{product_id}"
    for attempt in range(1, UPLOAD_RETRIES + 1):
        try:
            result = cloudinary.uploader.upload(
                str(file_path),
                public_id=public_id,
                overwrite=OVERWRITE_CLOUDINARY,
                resource_type="image",
                unique_filename=False
            )
            secure_url = result.get("secure_url")
            if secure_url:
                return secure_url
            else:
                logger.error(f"Upload succeeded but no secure_url for {file_path.name}")
                return None
        except Exception as e:
            logger.warning(f"Upload attempt {attempt} for {file_path.name} failed: {e}")
            if attempt < UPLOAD_RETRIES:
                time.sleep(RETRY_DELAY)
            else:
                logger.error(f"Upload failed after {UPLOAD_RETRIES} attempts: {file_path.name}")
                return None
    return None

# ----------------------------------------------------------------------
# MongoDB upsert (schema compliant)
# ----------------------------------------------------------------------
def upsert_mongo(collection, product_id: int, image_url: str, dry_run: bool) -> bool:
    """
    Upsert image metadata respecting the schema validator.
    - Sets image_type (required)
    - Sets created_at only on insert ($setOnInsert)
    - Updates updated_at on every upsert
    """
    if dry_run:
        logger.info(f"[DRY RUN] Would upsert product {product_id} with url {image_url}, type={IMAGE_TYPE}")
        return True

    now = datetime.now(timezone.utc)
    try:
        result = collection.update_one(
            {"owner_type": "product", "owner_id": product_id},
            {
                "$set": {
                    "image_url": image_url,
                    "image_type": IMAGE_TYPE,
                    "updated_at": now
                },
                "$setOnInsert": {
                    "created_at": now
                }
            },
            upsert=True
        )
        return True
    except PyMongoError as e:
        logger.error(f"MongoDB upsert failed for product {product_id}: {e}")
        return False

# ----------------------------------------------------------------------
# Main pipeline
# ----------------------------------------------------------------------
def scan_and_ingest(root_path: Path):
    if not root_path.exists():
        logger.error(f"Images root not found: {root_path}")
        sys.exit(1)

    webp_files = list(root_path.glob("*.webp"))
    if not webp_files:
        logger.warning(f"No .webp files found in {root_path}")
        return

    logger.info(f"Found {len(webp_files)} WebP files")

    init_cloudinary()
    mongo_collection = get_mongo_collection() if not DRY_RUN else None

    stats = {
        "total": len(webp_files),
        "uploaded": 0,
        "failed_upload": 0,
        "synced": 0,
        "failed_sync": 0,
        "skipped_invalid": 0
    }

    for file_path in tqdm(webp_files, desc="Processing images", unit="file"):
        product_id = validate_filename(file_path)
        if product_id is None:
            stats["skipped_invalid"] += 1
            continue

        image_url = upload_to_cloudinary(product_id, file_path, DRY_RUN)
        if image_url is None:
            stats["failed_upload"] += 1
            continue
        stats["uploaded"] += 1

        if not DRY_RUN:
            success = upsert_mongo(mongo_collection, product_id, image_url, DRY_RUN)
            if success:
                stats["synced"] += 1
            else:
                stats["failed_sync"] += 1
        else:
            stats["synced"] += 1

    print("\n" + "=" * 60)
    print("INGESTION SUMMARY")
    print("=" * 60)
    print(f"Total files scanned:  {stats['total']}")
    print(f"Invalid filenames:     {stats['skipped_invalid']}")
    print(f"Uploaded to Cloudinary:{stats['uploaded']}")
    print(f"Failed uploads:        {stats['failed_upload']}")
    print(f"Synced to MongoDB:     {stats['synced']}")
    if stats['failed_sync']:
        print(f"Failed MongoDB sync:   {stats['failed_sync']}")
    print("=" * 60)
    if DRY_RUN:
        print("DRY RUN – no changes were made.")
    else:
        print(f"Image type used: {IMAGE_TYPE}")

def parse_args():
    import argparse
    parser = argparse.ArgumentParser(description="Bulk image ingestion to Cloudinary + MongoDB")
    parser.add_argument("--dry-run", action="store_true", help="Simulate without uploading or DB writes")
    parser.add_argument("--root", type=str, help="Override IMAGES_ROOT")
    return parser.parse_args()

def main():
    args = parse_args()
    global DRY_RUN, IMAGES_ROOT
    if args.dry_run:
        DRY_RUN = True
        logger.info("DRY RUN mode enabled")
    root_path = Path(args.root) if args.root else Path(IMAGES_ROOT)
    scan_and_ingest(root_path)

if __name__ == "__main__":
    main()