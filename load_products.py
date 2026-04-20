import pandas as pd
import re
import unicodedata
from sqlalchemy import create_engine, text

DB_URL = "postgresql://postgres:yoruwanemurerukai@localhost:5433/vademecum"
engine = create_engine(DB_URL)

# =========================
# SAFE STRING
# =========================
def safe_str(value):
    if pd.isna(value):
        return ""
    return str(value)

def normalize_text(text):
    text = safe_str(text).strip()
    text = re.sub(r'\s+', ' ', text)
    return text if text else None

# =========================
# CLEAN COLUMNS
# =========================
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

# =========================
# HEADER DETECTION (SAFE)
# =========================
def detect_header(df):
    keywords = ["nombre", "comercial", "generico"]

    for i in range(len(df)):
        row = [safe_str(cell).lower() for cell in df.iloc[i]]
        matches = sum(any(k in cell for k in keywords) for cell in row)
        if matches >= 2:
            return i

    return 0

# =========================
# FIND COLUMN FLEXIBLY
# =========================
def find_column(df, keywords):
    for col in df.columns:
        if any(k in col for k in keywords):
            return col
    return None

# =========================
# SPLIT PRODUCTS
# =========================
def split_products(name):
    if not name:
        return []
    parts = re.split(r',|\/|\sy\s', name)
    return [p.strip() for p in parts if len(p.strip()) > 2]

# =========================
# DOSAGE INFERENCE
# =========================
def infer_dosage(form, notes):
    text = f"{form or ''} {notes or ''}".lower()

    if "unguent" in text:
        return "Unguento oftálmico"
    if "suspension" in text:
        return "Suspensión oftálmica"
    if "solucion" in text:
        return "Solución oftálmica"
    if "emulsion" in text:
        return "Emulsión oftálmica"

    return "Gotas oftálmicas"

# =========================
# CACHE SYSTEM (CRITICAL)
# =========================
family_cache = {}
lab_cache = {}
generic_cache = {}

def get_or_create(conn, table, name, cache):
    if not name:
        name = "Desconocido"

    if name in cache:
        return cache[name]

    result = conn.execute(
        text(f"SELECT id FROM {table} WHERE LOWER(name)=LOWER(:name)"),
        {"name": name}
    ).fetchone()

    if result:
        cache[name] = result[0]
        return result[0]

    result = conn.execute(
        text(f"INSERT INTO {table} (name) VALUES (:name) RETURNING id"),
        {"name": name}
    ).fetchone()

    cache[name] = result[0]
    return result[0]

# =========================
# PROCESS SHEET
# =========================
def process_sheet(sheet_name, df):
    print(f"\nProcessing {sheet_name}")

    header_row = detect_header(df)
    df.columns = df.iloc[header_row]
    df = df[(header_row + 1):]

    df = clean_columns(df)
    df = df.ffill()

    col_name = find_column(df, ["nombre comercial"])
    col_conc = find_column(df, ["concentr"])
    col_form = find_column(df, ["forma"])
    col_pos = find_column(df, ["posolog"])
    col_notes = find_column(df, ["nota"])
    col_family = find_column(df, ["famil"])
    col_lab = find_column(df, ["labor"])
    col_generic = find_column(df, ["generico"])

    inserted = 0

    with engine.begin() as conn:
        for _, row in df.iterrows():

            commercial_raw = normalize_text(row.get(col_name))
            if not commercial_raw:
                continue

            family = normalize_text(row.get(col_family))
            lab = normalize_text(row.get(col_lab))
            generic = normalize_text(row.get(col_generic))

            # CREATE / GET IDS
            family_id = get_or_create(conn, "families", family, family_cache)
            lab_id = get_or_create(conn, "laboratories", lab, lab_cache)
            generic_id = get_or_create(conn, "generics", generic, generic_cache)

            products = split_products(commercial_raw)

            for product_name in products:

                concentration = normalize_text(row.get(col_conc))
                posology = normalize_text(row.get(col_pos))
                notes = normalize_text(row.get(col_notes))

                dosage_form = infer_dosage(
                    normalize_text(row.get(col_form)),
                    notes
                )

                if not product_name:
                    continue

                conn.execute(text("""
                    INSERT INTO products
                    (family_id, laboratory_id, generic_id,
                     commercial_name, concentration, dosage_form, posology, notes, is_active)
                    VALUES (:fid, :lid, :gid, :name, :conc, :form, :pos, :notes, true)
                """), {
                    "fid": family_id,
                    "lid": lab_id,
                    "gid": generic_id,
                    "name": product_name,
                    "conc": concentration,
                    "form": dosage_form,
                    "pos": posology,
                    "notes": notes
                })

                inserted += 1

    print(f"{sheet_name} → inserted {inserted} cleaned products")
    return inserted

# =========================
# MAIN
# =========================
def main():
    print(DB_URL)

    try:
        with engine.connect():
            print("Connected to DB OK")
    except:
        print("DB connection failed")
        return

    file_path = "vademecumOptometria.xlsx"
    xls = pd.ExcelFile(file_path)

    total = 0

    for sheet in xls.sheet_names:
        df = pd.read_excel(file_path, sheet_name=sheet, header=None)
        total += process_sheet(sheet, df)

    print(f"\nTotal BEFORE COMMIT: {total}")
    print("✔ Data loaded successfully")

if __name__ == "__main__":
    main()