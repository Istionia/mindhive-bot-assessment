#!/usr/bin/env python3
import requests
import csv
import re
from pathlib import Path

# 1. Point this at your actual collection JSON
JSON_URL = "https://shop.zuscoffee.com/collections/tumbler/products.json?limit=250"
CSV_PATH = Path("data/zus_drinkware.csv")  # or tumbler.csv

# 2. Fetch the JSON
resp = requests.get(JSON_URL, timeout=10)
resp.raise_for_status()
data = resp.json()

products = data.get("products", [])
if not products:
    print("⚠️  No products returned. Check that JSON_URL is correct.")
    exit(1)

# 3. Write CSV
CSV_PATH.parent.mkdir(exist_ok=True, parents=True)
with open(CSV_PATH, "w", newline="", encoding="utf-8") as f:
    writer = csv.writer(f)
    writer.writerow(["id", "title", "content"])
    for i, p in enumerate(products, start=1):
        title = p.get("title", "").strip()
        body_html = p.get("body_html", "")
        # Strip HTML tags
        text = re.sub(r"<[^>]+>", "", body_html).strip()
        writer.writerow([i, title, text])

print(f"✅ Exported {len(products)} items to {CSV_PATH}")


