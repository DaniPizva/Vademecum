import os
import re
import unicodedata
import pandas as pd
import sqlalchemy
from sqlalchemy import create_engine, text as sql_text
from dotenv import load_dotenv

# Load environment variables
load_dotenv()
DB_URL = os.getenv("DB_URL")

if not DB_URL:
    raise ValueError("DB_URL not found in .env file")

# Print masked URL for verification
masked_url = DB_URL.replace("npg_L3FXZMrVxyg7", "***")
print(f"Connecting to: {masked_url}")

engine = create_engine(DB_URL)

# Import your models' Base to create tables
# Adjust the import path according to your project structure
try:
    from db.db import Base
    print("Creating tables if they don't exist...")
    Base.metadata.create_all(engine)
    print("Tables ready.")
except ImportError:
    print("Warning: Could not import Base from db.db. Assuming tables already exist.")

# ------------------------------------------------------------
# Helper functions (same as before)
# ------------------------------------------------------------
def safe_str(value):
    return "" if pd.isna(value) else str(value)

def normalize_text(txt):
    txt = safe_str(txt).strip()
    txt = re.sub(r'\s+', ' ', txt)
    return txt if txt else None

def clean_columns(df):
    df.columns = [
        unicodedata.normalize("NFKD", safe_str(col))
        .encode("ascii", "ignore")
        .decode("utf-8")
        .strip()
        .lower()
        for col in df.columns
    ]
    return df

def detect_header(df):
    keywords = ["nombre", "comercial", "generico", "familia"]
    for i in range(min(20, len(df))):
        row = [safe_str(cell).lower() for cell in df.iloc[i]]
        matches = sum(any(k in cell for k in keywords) for cell in row)
        if matches >= 2:
            return i
    return 0

def find_column(df, keywords):
    for col in df.columns:
        if any(k in col for k in keywords):
            return col
    return None

def split_products(name):
    if not name:
        return []
    parts = re.split(r',|\/|\sy\s', name)
    return [p.strip() for p in parts if len(p.strip()) > 2]

def infer_dosage(form, notes):
    text_val = f"{form or ''} {notes or ''}".lower()
    if "unguent" in text_val:
        return "Unguento oftálmico"
    if "suspension" in text_val:
        return "Suspensión oftálmica"
    if "solucion" in text_val:
        return "Solución oftálmica"
    if "emulsion" in text_val:
        return "Emulsión oftálmica"
    return "Gotas oftálmicas"

def extract_description_from_sheet(df, header_row):
    for i in range(header_row):
        cell = safe_str(df.iloc[i, 0])
        if len(cell) > 30 and any(k in cell.lower() for k in ["utilizan", "medicamentos", "infecciones", "reacciones"]):
            return normalize_text(cell)
        cell_b = safe_str(df.iloc[i, 1])
        if len(cell_b) > 30:
            return normalize_text(cell_b)
    return None

# ------------------------------------------------------------
# Caches
# ------------------------------------------------------------
therapeutic_cache = {}
description_cache = {}
family_cache = {}
lab_cache = {}
generic_cache = {}

def get_or_create_therapeutic(conn, name):
    if name in therapeutic_cache:
        return therapeutic_cache[name]
    res = conn.execute(sql_text("SELECT id FROM therapeutic_groups WHERE name = :name"), {"name": name}).fetchone()
    if res:
        therapeutic_cache[name] = res[0]
        return res[0]
    res = conn.execute(sql_text("INSERT INTO therapeutic_groups (name) VALUES (:name) RETURNING id"), {"name": name}).fetchone()
    therapeutic_cache[name] = res[0]
    return res[0]

def get_or_create_description(conn, desc_text, therapeutic_id):
    key = (desc_text, therapeutic_id)
    if key in description_cache:
        return description_cache[key]
    res = conn.execute(
        sql_text("SELECT id FROM descriptions WHERE description = :desc AND therapeutic_group_id = :tg_id"),
        {"desc": desc_text, "tg_id": therapeutic_id}
    ).fetchone()
    if res:
        description_cache[key] = res[0]
        return res[0]
    res = conn.execute(
        sql_text("INSERT INTO descriptions (description, therapeutic_group_id) VALUES (:desc, :tg_id) RETURNING id"),
        {"desc": desc_text, "tg_id": therapeutic_id}
    ).fetchone()
    description_cache[key] = res[0]
    return res[0]

def get_or_create_family(conn, name):
    if name in family_cache:
        return family_cache[name]
    res = conn.execute(sql_text("SELECT id FROM families WHERE name = :name"), {"name": name}).fetchone()
    if res:
        family_cache[name] = res[0]
        return res[0]
    res = conn.execute(sql_text("INSERT INTO families (name) VALUES (:name) RETURNING id"), {"name": name}).fetchone()
    family_cache[name] = res[0]
    return res[0]

def update_family(conn, family_id, description_id, mechanism):
    if description_id is None and mechanism is None:
        return
    params = {"fid": family_id}
    sets = []
    if description_id is not None:
        sets.append("description_id = :desc_id")
        params["desc_id"] = description_id
    if mechanism is not None:
        sets.append("mechanism_of_action = :mech")
        params["mech"] = mechanism
    if sets:
        query = f"UPDATE families SET {', '.join(sets)} WHERE id = :fid"
        conn.execute(sql_text(query), params)

def get_or_create_lab(conn, name):
    if name in lab_cache:
        return lab_cache[name]
    res = conn.execute(sql_text("SELECT id FROM laboratories WHERE LOWER(name)=LOWER(:name)"), {"name": name}).fetchone()
    if res:
        lab_cache[name] = res[0]
        return res[0]
    res = conn.execute(sql_text("INSERT INTO laboratories (name) VALUES (:name) RETURNING id"), {"name": name}).fetchone()
    lab_cache[name] = res[0]
    return res[0]

def get_or_create_generic(conn, name):
    if name in generic_cache:
        return generic_cache[name]
    res = conn.execute(sql_text("SELECT id FROM generics WHERE LOWER(name)=LOWER(:name)"), {"name": name}).fetchone()
    if res:
        generic_cache[name] = res[0]
        return res[0]
    res = conn.execute(sql_text("INSERT INTO generics (name) VALUES (:name) RETURNING id"), {"name": name}).fetchone()
    generic_cache[name] = res[0]
    return res[0]

# ------------------------------------------------------------
# Process sheet
# ------------------------------------------------------------
def process_sheet(sheet_name, df):
    print(f"\nProcessing sheet: {sheet_name}")

    header_row = detect_header(df)
    if header_row > 0:
        description_text = extract_description_from_sheet(df, header_row)
    else:
        description_text = None

    if not description_text:
        description_text = f"Medicamentos del grupo {sheet_name}"
        print(f"  No description found, using default: {description_text}")

    df.columns = df.iloc[header_row]
    df = df[(header_row + 1):]
    df = clean_columns(df)
    df = df.ffill()

    col_family = find_column(df, ["famil"])
    col_mechanism = find_column(df, ["mecanismo"])
    col_lab = find_column(df, ["labor"])
    col_generic = find_column(df, ["generico"])
    col_name = find_column(df, ["nombre comercial"])
    col_conc = find_column(df, ["concentr"])
    col_form = find_column(df, ["forma"])
    col_pos = find_column(df, ["posolog"])
    col_notes = find_column(df, ["nota"])

    if col_family is None:
        print(f"  ERROR: No 'familia' column found in sheet {sheet_name}. Skipping.")
        return 0

    with engine.begin() as conn:
        therapeutic_id = get_or_create_therapeutic(conn, sheet_name)
        description_id = get_or_create_description(conn, description_text, therapeutic_id)
        print(f"  Therapeutic group: {sheet_name} (id={therapeutic_id})")
        print(f"  Description id={description_id}")

        inserted_products = 0
        updated_families = set()

        for _, row in df.iterrows():
            family_name = normalize_text(row.get(col_family))
            if not family_name:
                continue

            mechanism = normalize_text(row.get(col_mechanism)) if col_mechanism else None
            family_id = get_or_create_family(conn, family_name)

            if family_id not in updated_families:
                update_family(conn, family_id, description_id, mechanism)
                updated_families.add(family_id)

            lab_name = normalize_text(row.get(col_lab)) if col_lab else None
            generic_name = normalize_text(row.get(col_generic)) if col_generic else None
            lab_id = get_or_create_lab(conn, lab_name) if lab_name else None
            generic_id = get_or_create_generic(conn, generic_name) if generic_name else None

            commercial_raw = normalize_text(row.get(col_name))
            if not commercial_raw:
                continue

            concentration = normalize_text(row.get(col_conc)) if col_conc else None
            posology = normalize_text(row.get(col_pos)) if col_pos else None
            notes = normalize_text(row.get(col_notes)) if col_notes else None
            dosage_form = infer_dosage(
                normalize_text(row.get(col_form)) if col_form else None,
                notes
            )

            products = split_products(commercial_raw)
            for prod_name in products:
                conn.execute(sql_text("""
                    INSERT INTO products
                    (family_id, laboratory_id, generic_id,
                     commercial_name, concentration, dosage_form, posology, notes, is_active)
                    VALUES (:fid, :lid, :gid, :name, :conc, :form, :pos, :notes, true)
                """), {
                    "fid": family_id,
                    "lid": lab_id,
                    "gid": generic_id,
                    "name": prod_name,
                    "conc": concentration,
                    "form": dosage_form,
                    "pos": posology,
                    "notes": notes
                })
                inserted_products += 1

        print(f"  → Inserted {inserted_products} products, updated {len(updated_families)} families")
        return inserted_products

# ------------------------------------------------------------
# Verification function
# ------------------------------------------------------------
def verify_counts():
    with engine.connect() as conn:
        tables = ["therapeutic_groups", "descriptions", "families", "products", "laboratories", "generics"]
        print("\n=== Row counts after load ===")
        for table in tables:
            result = conn.execute(sql_text(f"SELECT COUNT(*) FROM {table}")).fetchone()
            print(f"{table}: {result[0]} rows")

# ------------------------------------------------------------
# Main
# ------------------------------------------------------------
def main():
    confirm = input("This will DELETE ALL DATA from therapeutic_groups, descriptions, families, products, laboratories, generics. Proceed? (yes/no): ")
    if confirm.lower() != "yes":
        print("Aborted.")
        return

    with engine.begin() as conn:
        conn.execute(sql_text("TRUNCATE TABLE products, families, descriptions, therapeutic_groups, laboratories, generics RESTART IDENTITY CASCADE"))
        print("All related tables truncated.")

    file_path = "vademecumOptometria.xlsx"
    xls = pd.ExcelFile(file_path)
    total_products = 0

    for sheet in xls.sheet_names:
        df = pd.read_excel(file_path, sheet_name=sheet, header=None)
        total_products += process_sheet(sheet, df)

    print(f"\n✔ Complete! Total products inserted: {total_products}")
    verify_counts()

if __name__ == "__main__":
    main()