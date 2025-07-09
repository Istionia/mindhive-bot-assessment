import sqlite3
import csv
import os

DB_PATH = "db/outlets.db"
CSV_PATH = "data/zus_outlets.csv"

# Remove existing DB if needed
if os.path.exists(DB_PATH):
    os.remove(DB_PATH)

# Connect to DB
conn = sqlite3.connect(DB_PATH)
cursor = conn.cursor()

# Create table
cursor.execute("""
CREATE TABLE outlets (
    id INTEGER PRIMARY KEY,
    name TEXT,
    location TEXT,
    address TEXT,
    opening_time TEXT,
    closing_time TEXT,
    dine_in BOOLEAN,
    delivery BOOLEAN,
    pickup BOOLEAN
)
""")

# Read and insert CSV rows
with open(CSV_PATH, newline='', encoding='utf-8') as f:
    reader = csv.DictReader(f)
    for row in reader:
        cursor.execute("""
        INSERT INTO outlets (
            id, name, location, address,
            opening_time, closing_time,
            dine_in, delivery, pickup
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            int(row["id"]),
            row["name"],
            row["location"],
            row["address"],
            row["opening_time"],
            row["closing_time"],
            bool(int(row["dine_in"])),
            bool(int(row["delivery"])),
            bool(int(row["pickup"]))
        ))

with open("schema/outlet_schema.sql", "r") as schema_file:
    cursor.executescript(schema_file.read())

conn.commit()
conn.close()

print(f"✅ SQLite DB created at {DB_PATH}")
