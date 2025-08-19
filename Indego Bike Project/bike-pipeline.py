import requests
import datetime
import pandas as pd
from sqlalchemy import create_engine
from sqlalchemy.exc import SQLAlchemyError

# -------------------
# Step 1: Fetch the API
# -------------------
url = "https://api.citybik.es/v2/networks/indego"  # Philadelphia Indego
try:
    response = requests.get(url, timeout=10)
    response.raise_for_status()
    stations = response.json()["network"]["stations"]
except Exception as e:
    raise SystemExit(f"Failed to fetch Indego data: {e}")

print(f"✅ Fetched {len(stations)} stations from API")

# -------------------
# Step 2: Flatten JSON
# -------------------
records = []
for s in stations:
    record = {
        "id": s.get("id"),
        "name": s.get("name"),
        "latitude": s.get("latitude"),
        "longitude": s.get("longitude"),
        "free_bikes": s.get("free_bikes"),
        "empty_slots": s.get("empty_slots"),
        "timestamp": s.get("timestamp"),
        "ebikes": s.get("extra", {}).get("ebikes"),
        "has_ebikes": s.get("extra", {}).get("has_ebikes"),
        "last_updated": datetime.datetime.utcfromtimestamp(
            s.get("extra", {}).get("last_updated", 0)
        ) if s.get("extra", {}).get("last_updated") else None,
        "collected_at": datetime.datetime.utcnow()
    }
    records.append(record)

df = pd.DataFrame(records)
print("✅ Prepared DataFrame:")
print(df.head())

# -------------------
# Step 3: Connect to Google Cloud SQL
# -------------------
DB_USER = "postgres"                # e.g., postgres
DB_PASS = "Simfamily2!"            # the password you set
DB_HOST = "34.135.185.171"              # Cloud SQL public IP
DB_PORT = "5432"                         # default PostgreSQL port
DB_NAME = "postgres"                     # database name

engine_url = f"postgresql://{DB_USER}:{DB_PASS}@{DB_HOST}:{DB_PORT}/{DB_NAME}"

try:
    engine = create_engine(engine_url)
    with engine.connect() as conn:
        conn.execute("SELECT 1")  # test connection
    print(f"✅ Connected to Google Cloud SQL '{DB_NAME}' successfully")
except SQLAlchemyError as e:
    raise SystemExit(f"Database connection failed: {e}")

# -------------------
# Step 4: Create table
# -------------------
create_table_sql = """
CREATE TABLE IF NOT EXISTS station_status (
    id TEXT PRIMARY KEY,
    name TEXT,
    latitude FLOAT,
    longitude FLOAT,
    free_bikes INT,
    empty_slots INT,
    timestamp TIMESTAMP,
    ebikes INT,
    has_ebikes BOOLEAN,
    last_updated TIMESTAMP,
    collected_at TIMESTAMP
);
"""

with engine.begin() as conn:
    conn.execute(create_table_sql)
    print("✅ Table 'station_status' is ready")

# -------------------
# Step 5: Insert Data
# -------------------
try:
    df.to_sql("station_status", con=engine, if_exists="replace", index=False)
    print(f"✅ Inserted {len(df)} records into 'station_status'")
except SQLAlchemyError as e:
    raise SystemExit(f"Failed to insert data: {e}")

# -------------------
# Step 6: Verify insertion
# -------------------
with engine.connect() as conn:
    count = conn.execute("SELECT COUNT(*) FROM station_status").scalar()
    print(f"✅ Table now has {count} rows")
