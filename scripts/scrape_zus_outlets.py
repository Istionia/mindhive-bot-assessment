#!/usr/bin/env python3
# scripts/scrape_zus_outlets.py

import asyncio
import csv
from pathlib import Path
from playwright.async_api import async_playwright
import logging

# Configure logging
target = Path(__file__).resolve().parent.parent / 'data'
logging.basicConfig(level=logging.INFO, format='%(asctime)s [%(levelname)s] %(message)s')

BASE_URL = "https://zuscoffee.com/category/store/kuala-lumpur-selangor/page/{}/"
CSV_PATH = target / "zus_outlets.csv"

def ensure_data_dir():
    target.mkdir(parents=True, exist_ok=True)

async def scrape():
    ensure_data_dir()
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        page = await browser.new_page()

        with open(CSV_PATH, 'w', newline='', encoding='utf-8') as f:
            writer = csv.writer(f)
            writer.writerow([
                'id', 'name', 'location', 'address',
                'opening_time', 'closing_time',
                'dine_in', 'delivery', 'pickup'
            ])

            outlet_id = 1
            for page_num in range(1, 23):  # pages 1–22
                url = BASE_URL.format(page_num)
                logging.info(f"→ Page {page_num}: {url}")
                await page.goto(url)
                # Wait for rendered items
                try:
                    await page.wait_for_selector("article.elementor-post.elementor-grid-item", timeout=10000)
                except Exception:
                    logging.error(f"✖ No outlet articles found on page {page_num}")
                    break

                cards = await page.query_selector_all("article.elementor-post.elementor-grid-item")
                logging.info(f"  • Found {len(cards)} cards")

                for card in cards:
                    # Name
                    name_el = await card.query_selector("p.elementor-heading-title.elementor-size-default")
                    name = (await name_el.inner_text()).strip() if name_el else ""
                    # Location
                    loc_el = await card.query_selector("div.location h2 a")
                    location = (await loc_el.inner_text()).strip() if loc_el else "Unknown"
                    # Defaults
                    address = ""
                    opening_time, closing_time = "08:00", "22:00"
                    dine_in = delivery = pickup = 0

                    writer.writerow([
                        outlet_id, name, location, address,
                        opening_time, closing_time,
                        dine_in, delivery, pickup
                    ])
                    outlet_id += 1

        await browser.close()
        logging.info(f"✅ Scraped {outlet_id - 1} outlets into {CSV_PATH}")

if __name__ == '__main__':
    asyncio.run(scrape())
