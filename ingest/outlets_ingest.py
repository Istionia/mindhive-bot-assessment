# ingest/outlets_ingest.py
"""
Script to create and seed the SQLite database from CSV files.
Supports both outlets and drinkware tables.

Usage:
  python ingest/outlets_ingest.py \
      --outlets data/zus_outlets.csv \
      --drinkware data/zus_drinkware.csv \
      --db db/app_data.db
"""
import argparse
import sqlite3
import csv
import os
import logging
from pathlib import Path

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s"
)


def create_tables(conn):
    logging.info("Dropping existing tables if they exist...")
    conn.execute("DROP TABLE IF EXISTS outlets;")
    conn.execute("DROP TABLE IF EXISTS drinkware;")

    logging.info("Creating 'outlets' table...")
    conn.execute("""
        CREATE TABLE outlets (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            location TEXT NOT NULL,
            opening_time TEXT,
            closing_time TEXT,
            services TEXT
        );
    """
    )
    logging.info("Creating 'drinkware' table...")
    conn.execute("""
        CREATE TABLE drinkware (
            id INTEGER PRIMARY KEY,
            title TEXT NOT NULL,
            content TEXT
        );
    """
    )
    conn.commit()
    logging.info("Table creation complete.")


def seed_outlets(conn, csv_path):
    logging.info(f"Seeding 'outlets' from CSV: {csv_path}...")
    with open(csv_path, newline='', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        rows = []
        for idx, row in enumerate(reader, start=1):
            rows.append((
                row.get('name'),
                row.get('location'),
                row.get('opening_time'),
                row.get('closing_time'),
                row.get('services')
            ))
            if idx % 50 == 0:
                logging.info(f"  Processed {idx} outlet rows...")
    conn.executemany(
        "INSERT INTO outlets (name, location, opening_time, closing_time, services) VALUES (?, ?, ?, ?, ?);",
        rows
    )
    conn.commit()
    logging.info(f"Inserted {len(rows)} rows into 'outlets'.")


def seed_drinkware(conn, csv_path):
    logging.info(f"Seeding 'drinkware' from CSV: {csv_path}...")
    with open(csv_path, newline='', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        rows = []
        for idx, row in enumerate(reader, start=1):
            rows.append((
                int(row.get('id', idx)),
                row.get('title'),
                row.get('content')
            ))
            if idx % 50 == 0:
                logging.info(f"  Processed {idx} drinkware rows...")
    conn.executemany(
        "INSERT INTO drinkware (id, title, content) VALUES (?, ?, ?);",
        rows
    )
    conn.commit()
    logging.info(f"Inserted {len(rows)} rows into 'drinkware'.")


def main(outlets_csv: str, drinkware_csv: str, db_path: str):
    # Ensure output directory exists
    os.makedirs(os.path.dirname(db_path), exist_ok=True)
    logging.info(f"Connecting to SQLite DB at {db_path}...")
    conn = sqlite3.connect(db_path)
    try:
        create_tables(conn)
        if outlets_csv:
            seed_outlets(conn, outlets_csv)
        if drinkware_csv:
            seed_drinkware(conn, drinkware_csv)
        logging.info(f"Seeding complete. Database ready at {db_path}.")
    except Exception as e:
        logging.error(f"Error during seeding: {e}")
    finally:
        conn.close()
        logging.info("Database connection closed.")

if __name__ == '__main__':
    parser = argparse.ArgumentParser(description="Seed app SQLite database from CSVs.")
    parser.add_argument('--outlets', required=False, help='Path to outlets CSV file.')
    parser.add_argument('--drinkware', required=False, help='Path to drinkware CSV file.')
    parser.add_argument('--db', required=True, help='Output path for SQLite database.')
    args = parser.parse_args()

    if not args.outlets and not args.drinkware:
        parser.error("At least one of --outlets or --drinkware must be provided.")

    main(args.outlets, args.drinkware, args.db)
