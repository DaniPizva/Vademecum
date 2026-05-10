from db.mongo import get_mongo_db
from db.db import SessionLocal
from db.models import Product, ProductImage


def run_migration():
    mongo = get_mongo_db()
    db = SessionLocal()

    print("Starting migration...")

    # Load ALL valid products once (fast lookup set)
    products = db.query(Product).all()

    valid_ids = {p.id for p in products}
    name_map = {p.id: p.commercial_name for p in products}

    print(f"Valid products in DB: {len(valid_ids)}")

    docs = list(mongo["images"].find({"owner_type": "product"}))

    print(f"Mongo images found: {len(docs)}")

    seen_main = set()
    inserted = 0
    skipped = 0

    for doc in docs:
        product_id = doc.get("owner_id")
        image_url = doc.get("image_url")

        # 🔴 GUARD 1: product must exist in Postgres
        if product_id not in valid_ids:
            skipped += 1
            print(f"[SKIP] product_id {product_id} not found in PostgreSQL")
            continue

        # 🔴 GUARD 2 (optional sanity check via name match)
        # only used if you want extra strict validation
        # if name_map[product_id] not in some_expected_rule:
        #     continue

        is_main = product_id not in seen_main
        seen_main.add(product_id)

        try:
            img = ProductImage(
                product_id=product_id,
                image_url=image_url,
                is_main=is_main
            )

            db.add(img)
            inserted += 1

        except Exception as e:
            print(f"[ERROR] failed inserting product_id={product_id}: {e}")
            skipped += 1
            continue

    # commit only after full loop
    try:
        db.commit()
        print("Commit successful")
    except Exception as e:
        db.rollback()
        print(f"Commit failed: {e}")
    finally:
        db.close()

    print("\n--- MIGRATION SUMMARY ---")
    print(f"Inserted: {inserted}")
    print(f"Skipped: {skipped}")
    
if __name__ == "__main__":
    run_migration()