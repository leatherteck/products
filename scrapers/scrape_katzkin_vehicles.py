import requests
import json
import time
from bs4 import BeautifulSoup
import csv
import os

# Base URL for Katzkin API endpoints
BASE_URL = "http://www.katzkinvis.com/interiorselector/getExtData/"
CHECKPOINT_FILE = "katzkin_scraper_checkpoint.json"
CHECKPOINT_INTERVAL = 50  # Save progress every 50 vehicles

def fetch_years():
    """Fetch all available years"""
    print("Fetching years...")
    url = f"{BASE_URL}katzkinGetYears_mobile.php?mpr=false&resetVars=false"
    response = requests.get(url)

    if response.status_code == 200:
        soup = BeautifulSoup(response.text, 'html.parser')
        select = soup.find('select', {'id': 'years'})
        if select:
            years = [option['value'] for option in select.find_all('option') if option['value'] != 'select']
            print(f"Found {len(years)} years")
            return years
    return []

def fetch_makes(year):
    """Fetch all makes for a given year"""
    print(f"Fetching makes for {year}...")
    url = f"{BASE_URL}katzkinGetMakes_mobile.php?mpr=false&year={year}&resetVars=false"
    response = requests.get(url)

    if response.status_code == 200:
        soup = BeautifulSoup(response.text, 'html.parser')
        select = soup.find('select', {'id': 'makes'})
        if select:
            makes = [option['value'] for option in select.find_all('option')
                    if option['value'] not in ['select', 'dontseemyoption']]
            print(f"  Found {len(makes)} makes for {year}")
            return makes
    return []

def fetch_models(year, make):
    """Fetch all models for a given year and make"""
    print(f"  Fetching models for {year} {make}...")
    url = f"{BASE_URL}katzkinGetModels_mobile.php?make={make}&year={year}"
    response = requests.get(url)

    if response.status_code == 200:
        soup = BeautifulSoup(response.text, 'html.parser')
        select = soup.find('select', {'id': 'models'})
        if select:
            models = [option['value'] for option in select.find_all('option')
                     if option['value'] not in ['select', 'dontseemyoption']]
            print(f"    Found {len(models)} models")
            return models
    return []

def fetch_trims(year, make, model):
    """Fetch all trims for a given year, make, and model"""
    print(f"    Fetching trims for {year} {make} {model}...")
    url = f"{BASE_URL}katzkinGetTrims_mobile.php?make={make}&model={model}&year={year}"
    response = requests.get(url)

    if response.status_code == 200:
        soup = BeautifulSoup(response.text, 'html.parser')
        select = soup.find('select', {'id': 'trims'})
        if select:
            trims = [option['value'] for option in select.find_all('option')
                    if option['value'] not in ['select', 'dontseemyoption']]
            print(f"      Found {len(trims)} trims")
            return trims
    return []

def fetch_designs(year, make, model, trim):
    """Fetch design/VIS codes for a specific vehicle"""
    print(f"      Fetching designs for {year} {make} {model} {trim}...")
    url = f"{BASE_URL}katzkinGetVISCodes_mobile.php?make={make}&model={model}&year={year}&trim={trim}"

    try:
        response = requests.get(url, timeout=10)
        if response.status_code == 200:
            text = response.text

            # Extract design numbers from the response
            # Format: "F1274-100 - model_year_id = 1461" or "K1093-100 - model_year_id = 1334"
            import re
            design_pattern = r'([KF]\d{1,4}-\d{3})'
            designs = re.findall(design_pattern, text)

            # Remove duplicates while preserving order
            unique_designs = []
            seen = set()
            for design in designs:
                if design not in seen:
                    seen.add(design)
                    unique_designs.append(design)

            print(f"        Found {len(unique_designs)} design numbers")
            return unique_designs
    except Exception as e:
        print(f"        [WARNING] Could not fetch designs: {e}")

    return []

def load_checkpoint():
    """Load checkpoint file if it exists"""
    if os.path.exists(CHECKPOINT_FILE):
        with open(CHECKPOINT_FILE, 'r') as f:
            checkpoint = json.load(f)
            print(f"[CHECKPOINT] Resuming from checkpoint: {len(checkpoint['vehicles'])} vehicles already scraped")
            return checkpoint
    return {'vehicles': [], 'completed_combinations': set()}

def save_checkpoint(vehicles, completed_combinations):
    """Save current progress to checkpoint file"""
    checkpoint = {
        'vehicles': vehicles,
        'completed_combinations': list(completed_combinations)  # Convert set to list for JSON
    }
    with open(CHECKPOINT_FILE, 'w') as f:
        json.dump(checkpoint, f, indent=2)
    print(f"[CHECKPOINT] Progress saved: {len(vehicles)} vehicles")

def scrape_all_vehicles(max_vehicles=None):
    """Scrape all vehicle combinations with checkpoint support"""

    # Load existing checkpoint
    checkpoint = load_checkpoint()
    all_vehicles = checkpoint['vehicles']
    completed_combinations = set(checkpoint['completed_combinations'])

    # Fetch years
    years = fetch_years()

    for year in years:
        # Fetch makes for this year
        makes = fetch_makes(year)
        time.sleep(0.5)  # Be respectful with requests

        for make in makes:
            # Fetch models for this year+make
            models = fetch_models(year, make)
            time.sleep(0.5)

            for model in models:
                # Fetch trims for this year+make+model
                trims = fetch_trims(year, make, model)
                time.sleep(0.5)

                for trim in trims:
                    # Create unique key for this vehicle combination
                    vehicle_key = f"{year}|{make}|{model}|{trim}"

                    # Skip if already scraped
                    if vehicle_key in completed_combinations:
                        print(f"        [SKIP] Already scraped: {year} {make} {model} {trim}")
                        continue

                    # Fetch design numbers for this vehicle
                    design_numbers = fetch_designs(year, make, model, trim)
                    time.sleep(0.5)

                    vehicle = {
                        'year': year,
                        'make': make,
                        'model': model,
                        'trim': trim,
                        'design_numbers': design_numbers,
                        'design_count': len(design_numbers) if design_numbers else 0
                    }
                    all_vehicles.append(vehicle)
                    completed_combinations.add(vehicle_key)
                    print(f"        [OK] Added: {year} {make} {model} {trim} ({len(design_numbers)} designs)")

                    # Save checkpoint every N vehicles
                    if len(all_vehicles) % CHECKPOINT_INTERVAL == 0:
                        save_checkpoint(all_vehicles, completed_combinations)

                    # Stop if we've reached the max limit
                    if max_vehicles and len(all_vehicles) >= max_vehicles:
                        print(f"\n[INFO] Reached limit of {max_vehicles} vehicles. Stopping...")
                        save_checkpoint(all_vehicles, completed_combinations)
                        return all_vehicles

    # Final checkpoint save
    save_checkpoint(all_vehicles, completed_combinations)
    return all_vehicles

def save_to_csv(vehicles, filename='katzkin_vehicles.csv'):
    """Save vehicles to CSV file with one row per design number"""
    print(f"\nSaving {len(vehicles)} vehicles to {filename}...")
    with open(filename, 'w', newline='', encoding='utf-8') as f:
        writer = csv.DictWriter(f, fieldnames=['year', 'make', 'model', 'trim', 'design_number'])
        writer.writeheader()

        for v in vehicles:
            design_numbers = v.get('design_numbers', [])

            if design_numbers:
                # Create one row for each design number
                for design_num in design_numbers:
                    writer.writerow({
                        'year': v['year'],
                        'make': v['make'],
                        'model': v['model'],
                        'trim': v['trim'],
                        'design_number': design_num
                    })
            else:
                # If no design numbers, still write the vehicle with empty design
                writer.writerow({
                    'year': v['year'],
                    'make': v['make'],
                    'model': v['model'],
                    'trim': v['trim'],
                    'design_number': ''
                })
    print(f"[OK] Saved to {filename}")

def save_to_json(vehicles, filename='katzkin_vehicles.json'):
    """Save vehicles to JSON file"""
    print(f"Saving {len(vehicles)} vehicles to {filename}...")
    with open(filename, 'w', encoding='utf-8') as f:
        json.dump(vehicles, f, indent=2)
    print(f"[OK] Saved to {filename}")

if __name__ == "__main__":
    print("=== Katzkin Vehicle Scraper ===\n")
    print("This will scrape all vehicle combinations from Katzkin's dropdown system.")
    print("This may take a while...\n")

    # Set to 10 for testing, None for full scrape
    MAX_VEHICLES = None
    print(f"[TEST MODE] Limiting to {MAX_VEHICLES} vehicles\n")

    try:
        vehicles = scrape_all_vehicles(max_vehicles=MAX_VEHICLES)

        print(f"\n=== Results ===")
        print(f"Total vehicles scraped: {len(vehicles)}")

        # Save to both CSV and JSON
        save_to_csv(vehicles)
        save_to_json(vehicles)

        print("\n[OK] Scraping complete!")

    except Exception as e:
        print(f"\n[ERROR] Error: {e}")
        import traceback
        traceback.print_exc()
