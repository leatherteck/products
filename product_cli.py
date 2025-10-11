#!/usr/bin/env python3
"""
LeatherTek Product Management CLI
Centralized tool for all product data operations
"""

import json
import re
import sys
from pathlib import Path

def load_products():
    """Load products.json"""
    with open('products.json', 'r', encoding='utf-8') as f:
        return json.load(f)

def save_products(products):
    """Save products.json"""
    with open('products.json', 'w', encoding='utf-8') as f:
        json.dump(products, f, indent=2, ensure_ascii=False)

def clean_trims(dry_run=False):
    """Remove design numbers and error codes from trim field"""
    products = load_products()
    cleaned_count = 0

    for product in products:
        trim = product.get('trim', '')
        if trim:
            original_trim = trim

            # Remove design number with dash (e.g., "LX K1234-100" -> "LX")
            trim = re.sub(r'\s+[KFL]\d{1,4}-\d{2,4}\b.*$', '', trim)

            # Remove design number without dash (e.g., "LX K3350121" -> "LX")
            trim = re.sub(r'\s+[KFL]\d{4,7}\b.*$', '', trim)

            # Remove short design codes (e.g., "STX K22" -> "STX")
            trim = re.sub(r'\s+[KFL]\d{1,3}\b.*$', '', trim)

            # Remove parenthetical codes (e.g., "(Code Error)", "(CODE NA)")
            trim = re.sub(r'\s*\([^)]+\)\s*$', '', trim)

            # Remove incomplete parenthetical codes
            trim = re.sub(r'\s+[KFL]\s*\([^)]*$', '', trim)

            trim = trim.strip()

            if trim != original_trim:
                if dry_run:
                    print(f"  {original_trim} -> {trim}")
                else:
                    product['trim'] = trim
                cleaned_count += 1

    if not dry_run:
        save_products(products)

    return cleaned_count

def fill_missing_trims(source='all'):
    """Fill missing trims from Excel and Katzkin data"""
    import pandas as pd
    import csv

    products = load_products()

    # Load Excel trim map
    excel_trim_map = {}
    if source in ['all', 'excel']:
        try:
            df = pd.read_excel('data/current.xlsx')
            for _, row in df.iterrows():
                tags = str(row.get('Tags', ''))
                title = str(row.get('Title', ''))
                tag_list = [t.strip() for t in tags.split(',')]

                design_num = ""
                for tag in tag_list:
                    if re.match(r'^[KFL]\d{1,4}-\d{2,4}$', tag, re.IGNORECASE):
                        design_num = tag.upper()
                        break

                # Parse trim from title
                for_match = re.search(r'\bfor\s+(.+?)(?:\s+(?:19|20)\d{2}|$)', title, re.IGNORECASE)
                if for_match and design_num:
                    vehicle_part = for_match.group(1).strip()
                    words = vehicle_part.split()
                    if len(words) >= 3:
                        trim = ' '.join(words[2:])
                        excel_trim_map[design_num] = trim

            print(f"Loaded {len(excel_trim_map)} trims from Excel")
        except FileNotFoundError:
            print("Warning: data/current.xlsx not found")

    # Load Katzkin trim map
    katzkin_trim_map = {}
    if source in ['all', 'katzkin']:
        try:
            with open('katzkin_from_excel.csv', 'r', encoding='utf-8') as f:
                reader = csv.DictReader(f)
                for row in reader:
                    design_num = row.get('design_number', '').strip().upper()
                    trim = row.get('trim', '').strip().upper()
                    if design_num and trim:
                        katzkin_trim_map[design_num] = trim

            print(f"Loaded {len(katzkin_trim_map)} trims from Katzkin CSV")
        except FileNotFoundError:
            print("Warning: katzkin_from_excel.csv not found")

    # Fill missing trims
    updated_from_excel = 0
    updated_from_katzkin = 0

    for product in products:
        if not product.get('trim'):
            design_num = product.get('designNumber', '')
            if design_num:
                if design_num in excel_trim_map:
                    product['trim'] = excel_trim_map[design_num]
                    updated_from_excel += 1
                elif design_num in katzkin_trim_map:
                    product['trim'] = katzkin_trim_map[design_num]
                    updated_from_katzkin += 1

    save_products(products)

    return updated_from_excel, updated_from_katzkin

def add_products_from_excel(excel_file):
    """Add new products from Excel file"""
    import pandas as pd

    products = load_products()
    existing_count = len(products)

    df = pd.read_excel(excel_file, header=None)
    new_products = []

    for _, row in df.iterrows():
        design_name = str(row[0]).strip() if pd.notna(row[0]) else ""
        make = str(row[1]).strip() if pd.notna(row[1]) else ""
        model = str(row[2]).strip() if pd.notna(row[2]) else ""
        trim = str(row[3]).strip() if pd.notna(row[3]) else ""
        year = str(row[4]).strip() if pd.notna(row[4]) else ""
        description = str(row[5]).strip() if pd.notna(row[5]) else ""
        design_number = str(row[6]).strip() if pd.notna(row[6]) else ""
        image = str(row[7]).strip() if pd.notna(row[7]) else ""

        if not make or make == 'nan' or not model or model == 'nan':
            continue

        name = f"{design_name} for {make} {model} {trim} {year}".strip()

        product = {
            "year": year,
            "make": make,
            "model": model,
            "trim": trim,
            "name": name,
            "price": "$1895.00",
            "image": image if image != 'nan' else "",
            "url": ""
        }

        if design_name and design_name != trim:
            product["design"] = design_name

        if design_number and design_number != 'nan':
            product["designNumber"] = design_number

        new_products.append(product)

    products.extend(new_products)
    save_products(products)

    return len(new_products)

def fetch_urls():
    """Fetch URLs for products without URLs from GHL API"""
    import requests
    import time

    PRODUCTS_API_URL = "https://backend.leadconnectorhq.com/products/public"
    PRODUCT_DETAILS_BASE_URL = "https://leatherteck.com/item-details/product"

    API_DEFAULT_PARAMS = {
        "limit": 500,
        "offset": 0,
        "locationId": "dC0ujeVga1kZlZsLqjZz",
        "storeId": "y9c89s3eZFhBWlHj67aF",
        "sendWishlistStatus": "false",
        "sortField": "amount",
        "sortOrder": "asc"
    }
    REQUEST_HEADERS = {
        "accept": "application/json"
    }

    def build_product_url(product_id):
        if product_id:
            return f"{PRODUCT_DETAILS_BASE_URL}/{product_id}"
        return ""

    products = load_products()

    # Find products without URLs
    products_without_url = [p for p in products if not p.get("url")]
    design_numbers_needed = {}
    for p in products_without_url:
        design_num = p.get("designNumber", "").strip()
        if design_num:
            design_numbers_needed[design_num] = p

    print(f"Found {len(products_without_url)} products without URLs")
    print(f"Design numbers to search: {len(design_numbers_needed)}\n")

    # Fetch ALL products from GHL
    print("Fetching all products from GHL API...")
    design_to_url = {}
    offset = 0

    while True:
        params = API_DEFAULT_PARAMS.copy()
        params["offset"] = offset
        print(f"  Fetching offset {offset}...")

        try:
            response = requests.get(PRODUCTS_API_URL, params=params, headers=REQUEST_HEADERS, timeout=30)
            response.raise_for_status()
            payload = response.json()

            items = payload.get("products", [])
            print(f"  Retrieved {len(items)} items")

            if not items:
                break

            # Build design number -> product ID mapping
            for item in items:
                product_id = item.get("_id")
                name = item.get("name", "")
                slug = item.get("slug", "")

                design_match = re.search(r'\b([KFL]\d{1,4}-\d{2,4})\b', f"{name} {slug}", re.IGNORECASE)
                if design_match and product_id:
                    design_num = design_match.group(1).upper()
                    if design_num in design_numbers_needed:
                        url = build_product_url(product_id)
                        design_to_url[design_num] = url
                        print(f"    Found: {design_num} -> {url}")

            if len(items) < API_DEFAULT_PARAMS["limit"]:
                break

            offset += API_DEFAULT_PARAMS["limit"]
            time.sleep(0.1)

        except Exception as e:
            print(f"  Error: {e}")
            break

    print(f"\nFound URLs for {len(design_to_url)} design numbers")

    # Update products with URLs
    updated_count = 0
    for design_num, url in design_to_url.items():
        if design_num in design_numbers_needed:
            product = design_numbers_needed[design_num]
            product["url"] = url
            updated_count += 1

    save_products(products)

    return updated_count, len(products_without_url) - updated_count

def stats():
    """Show product statistics"""
    products = load_products()

    total = len(products)
    with_url = len([p for p in products if p.get('url')])
    without_url = total - with_url
    with_trim = len([p for p in products if p.get('trim')])
    without_trim = total - with_trim
    with_design_num = len([p for p in products if p.get('designNumber')])

    print(f"\n=== Product Statistics ===")
    print(f"Total products: {total}")
    print(f"With URL: {with_url}")
    print(f"Without URL: {without_url}")
    print(f"With trim: {with_trim}")
    print(f"Without trim: {without_trim}")
    print(f"With design number: {with_design_num}")

def main():
    if len(sys.argv) < 2:
        print("""
LeatherTek Product Management CLI

Usage:
  python product_cli.py stats                    - Show product statistics
  python product_cli.py clean-trims             - Clean design numbers from trims
  python product_cli.py clean-trims --dry-run   - Preview trim cleaning
  python product_cli.py fill-trims              - Fill missing trims from all sources
  python product_cli.py fill-trims --excel      - Fill from Excel only
  python product_cli.py fill-trims --katzkin    - Fill from Katzkin only
  python product_cli.py add-products <file.xlsx> - Add products from Excel
  python product_cli.py fetch-urls              - Fetch URLs for products without URLs
        """)
        sys.exit(1)

    command = sys.argv[1]

    if command == 'stats':
        stats()

    elif command == 'clean-trims':
        dry_run = '--dry-run' in sys.argv
        if dry_run:
            print("\n=== Preview: Trims to be cleaned ===")

        count = clean_trims(dry_run=dry_run)

        if dry_run:
            print(f"\nWould clean {count} trims")
        else:
            print(f"\nCleaned {count} trims")
            stats()

    elif command == 'fill-trims':
        source = 'all'
        if '--excel' in sys.argv:
            source = 'excel'
        elif '--katzkin' in sys.argv:
            source = 'katzkin'

        excel_count, katzkin_count = fill_missing_trims(source=source)
        print(f"\nUpdated {excel_count} trims from Excel")
        print(f"Updated {katzkin_count} trims from Katzkin")
        stats()

    elif command == 'add-products':
        if len(sys.argv) < 3:
            print("Error: Please specify Excel file")
            sys.exit(1)

        excel_file = sys.argv[2]
        count = add_products_from_excel(excel_file)
        print(f"\nAdded {count} new products")
        stats()

    elif command == 'fetch-urls':
        updated, still_missing = fetch_urls()
        print(f"\nUpdated {updated} products with URLs")
        print(f"Still missing URLs: {still_missing}")
        stats()

    else:
        print(f"Unknown command: {command}")
        sys.exit(1)

if __name__ == '__main__':
    main()
