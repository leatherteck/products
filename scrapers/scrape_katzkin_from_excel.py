import pandas as pd
import requests
import json
import time
from bs4 import BeautifulSoup
import csv
import re

# Base URL for Katzkin API endpoints
BASE_URL = "http://www.katzkinvis.com/interiorselector/getExtData/"

def fetch_trims(year, make, model):
    """Fetch all trims for a given year, make, and model from Katzkin"""
    print(f"  Fetching trims for {year} {make} {model}...")
    url = f"{BASE_URL}katzkinGetTrims_mobile.php?make={make}&model={model}&year={year}"

    try:
        response = requests.get(url, timeout=10)
        if response.status_code == 200:
            soup = BeautifulSoup(response.text, 'html.parser')
            select = soup.find('select', {'id': 'trims'})
            if select:
                trims = [option['value'] for option in select.find_all('option')
                        if option['value'] not in ['select', 'dontseemyoption']]
                print(f"    Found {len(trims)} trims")
                return trims
    except Exception as e:
        print(f"    [WARNING] Could not fetch trims: {e}")

    return []

def fetch_designs(year, make, model, trim):
    """Fetch design/VIS codes for a specific vehicle from Katzkin"""
    print(f"    Fetching designs for {year} {make} {model} {trim}...")
    url = f"{BASE_URL}katzkinGetVISCodes_mobile.php?make={make}&model={model}&year={year}&trim={trim}"

    try:
        response = requests.get(url, timeout=10)
        if response.status_code == 200:
            text = response.text
            # Extract design numbers (format: F1274-100, K1093-100, etc.)
            design_pattern = r'([KF]\d{1,4}-\d{3})'
            designs = re.findall(design_pattern, text)

            # Remove duplicates while preserving order
            unique_designs = []
            seen = set()
            for design in designs:
                if design not in seen:
                    seen.add(design)
                    unique_designs.append(design)

            print(f"      Found {len(unique_designs)} design numbers")
            return unique_designs
    except Exception as e:
        print(f"      [WARNING] Could not fetch designs: {e}")

    return []

def get_vehicles_from_excel(excel_file):
    """Extract unique year/make/model combinations from EM Upholstery Excel"""
    print(f"Reading Excel file: {excel_file}")
    df = pd.read_excel(excel_file)

    # Get unique year/make/model combinations
    vehicles = df[['Year', 'Car Brand', 'Car Unit']].drop_duplicates()

    # Clean up year ranges (e.g., "2015- 2023" -> just get years)
    results = []
    for _, row in vehicles.iterrows():
        year = str(row['Year']).strip()
        make = str(row['Car Brand']).strip()
        model = str(row['Car Unit']).strip()

        # Handle year ranges
        if '-' in year:
            # For ranges like "2015- 2023", we'll use the end year for Katzkin search
            parts = year.replace(' ', '').split('-')
            if len(parts) == 2 and parts[1]:
                year = parts[1]  # Use the latest year

        results.append({
            'year': year,
            'make': make,
            'model': model
        })

    print(f"Found {len(results)} unique year/make/model combinations in Excel\n")
    return results

def scrape_katzkin_for_excel_vehicles(excel_file='data/EM Upholstery Technology.xlsx'):
    """Scrape Katzkin for all vehicles found in Excel"""

    # Get vehicles from Excel
    excel_vehicles = get_vehicles_from_excel(excel_file)

    all_results = []

    for i, vehicle in enumerate(excel_vehicles, 1):
        year = vehicle['year']
        make = vehicle['make']
        model = vehicle['model']

        print(f"\n[{i}/{len(excel_vehicles)}] Processing: {year} {make} {model}")

        # Fetch trims from Katzkin
        trims = fetch_trims(year, make, model)
        time.sleep(0.5)

        if not trims:
            print(f"  [WARNING] No trims found for {year} {make} {model}")
            continue

        # Fetch designs once for the first trim (all trims share same designs)
        designs = []
        if trims:
            first_trim = trims[0]
            designs = fetch_designs(year, make, model, first_trim)
            time.sleep(0.5)

        # Store each trim with the same design numbers
        for trim in trims:
            result = {
                'year': year,
                'make': make,
                'model': model,
                'trim': trim,
                'design_numbers': designs,
                'design_count': len(designs)
            }
            all_results.append(result)
            print(f"      [OK] {year} {make} {model} {trim} - {len(designs)} designs (shared)")

    return all_results

def save_results(results, csv_file='katzkin_from_excel.csv', json_file='katzkin_from_excel.json'):
    """Save results to CSV and JSON"""

    # Save CSV (one row per design)
    print(f"\nSaving to {csv_file}...")
    with open(csv_file, 'w', newline='', encoding='utf-8') as f:
        writer = csv.DictWriter(f, fieldnames=['year', 'make', 'model', 'trim', 'design_number'])
        writer.writeheader()

        for result in results:
            for design in result['design_numbers']:
                writer.writerow({
                    'year': result['year'],
                    'make': result['make'],
                    'model': result['model'],
                    'trim': result['trim'],
                    'design_number': design
                })
    print(f"[OK] Saved to {csv_file}")

    # Save JSON
    print(f"Saving to {json_file}...")
    with open(json_file, 'w', encoding='utf-8') as f:
        json.dump(results, f, indent=2)
    print(f"[OK] Saved to {json_file}")

if __name__ == "__main__":
    print("=== Katzkin Scraper (Excel-based) ===\n")
    print("This will scrape Katzkin for all vehicles in EM Upholstery Excel\n")

    try:
        results = scrape_katzkin_for_excel_vehicles()

        print(f"\n=== Results ===")
        print(f"Total vehicle-trim combinations scraped: {len(results)}")

        # Save results
        save_results(results)

        print("\n[OK] Scraping complete!")

    except Exception as e:
        print(f"\n[ERROR] Error: {e}")
        import traceback
        traceback.print_exc()
