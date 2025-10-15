import requests
import json
import re
import time

# Output files
PRODUCTS_JSON = "products.json"
UNMATCHED_JSON = "unmatched.json"
DROPDOWN_DATA = "dropdown_data.js"

STORE_BASE_URL = "https://leatherteck.com/store"
PRODUCT_DETAILS_BASE_URL = "https://leatherteck.com/item-details/product"
PRODUCTS_API_URL = "https://backend.leadconnectorhq.com/products/public"
API_PAGE_SIZE = 500
API_DEFAULT_PARAMS = {
    "limit": API_PAGE_SIZE,
    "offset": 0,
    "locationId": "dC0ujeVga1kZlZsLqjZz",
    "storeId": "y9c89s3eZFhBWlHj67aF",
    "sendWishlistStatus": "false",
    "sortField": "amount",
    "sortOrder": "asc",
    "collectionSlug": "",
    "productIds": ""
}
REQUEST_HEADERS = {
    "accept": "application/json"
}

DETAIL_REQUEST_PARAMS = {
    "locationId": API_DEFAULT_PARAMS["locationId"],
    "storeId": API_DEFAULT_PARAMS["storeId"]
}

STORE_PRODUCT_PATH = "product"


def clean_text(value):
    """Normalize whitespace and strip surrounding spaces."""
    if value is None:
        return ""
    text = str(value).replace("\n", " ").strip()
    return re.sub(r"\s+", " ", text)

def fetch_image_url(item):
    """Return the best image URL for a product record."""
    image_url = (item.get("image") or "").strip()
    if image_url:
        return image_url

    product_id = item.get("_id")
    if product_id:
        try:
            response = requests.get(
                f"{PRODUCTS_API_URL}/{product_id}",
                params=DETAIL_REQUEST_PARAMS,
                headers=REQUEST_HEADERS,
                timeout=30
            )
            response.raise_for_status()
            detail = response.json()
        except requests.RequestException as exc:
            print(f"    Failed image lookup for {product_id}: {exc}")
        except ValueError as exc:
            print(f"    Failed to decode image payload for {product_id}: {exc}")
        else:
            medias = detail.get("medias") or detail.get("media") or []
            for media in medias:
                url = media.get("url")
                if isinstance(url, str) and url.strip():
                    return url.strip()

            product_data = detail.get("product")
            if isinstance(product_data, dict):
                for key in ("featuredImage", "featuredMedia", "image"):
                    url = product_data.get(key)
                    if isinstance(url, str) and url.strip():
                        return url.strip()
                for key in ("medias", "images", "gallery"):
                    gallery = product_data.get(key) or []
                    for entry in gallery:
                        url = entry.get("url")
                        if isinstance(url, str) and url.strip():
                            return url.strip()

            for key in ("productImages", "images", "gallery"):
                gallery = detail.get(key) or []
                for entry in gallery:
                    url = entry.get("url") if isinstance(entry, dict) else entry
                    if isinstance(url, str) and url.strip():
                        return url.strip()

    slug = item.get("slug")
    if slug:
        page_url = f"{STORE_BASE_URL}/{slug}"
        try:
            response = requests.get(page_url, timeout=30)
            response.raise_for_status()
            match = re.search(r'<meta[^>]+property="og:image"[^>]+content="([^"]+)"', response.text, re.IGNORECASE)
            if match:
                return match.group(1).strip()
        except requests.RequestException as exc:
            print(f"    Failed store page image lookup for {page_url}: {exc}")



def build_product_url(item):
    """Return the item-details URL when possible, otherwise fall back to slug."""
    product_id = (item.get("_id") or "").strip()
    if product_id:
        return f"{PRODUCT_DETAILS_BASE_URL}/{product_id}"

    slug = (item.get("slug") or "").strip().strip('/')
    if slug:
        if slug.startswith(STORE_PRODUCT_PATH + "/"):
            slug_path = slug
        else:
            slug_path = f"{STORE_PRODUCT_PATH}/{slug}"
        return f"{STORE_BASE_URL}/{slug_path}"

    return ""


# --------------------------------------------------------------------
# 1. Load Katzkin trim data for fast lookup
# --------------------------------------------------------------------
import csv

KATZKIN_CSV_PATH = "katzkin_from_excel.csv"
KATZKIN_TRIM_MAP = {}  # design_number -> trim lookup

try:
    with open(KATZKIN_CSV_PATH, 'r', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        for row in reader:
            design_num = row.get('design_number', '').strip()
            trim = row.get('trim', '').strip().upper()
            if design_num and trim:
                KATZKIN_TRIM_MAP[design_num] = trim
    print(f"Loaded {len(KATZKIN_TRIM_MAP)} Katzkin trim mappings from CSV")
except FileNotFoundError:
    print(f"Warning: {KATZKIN_CSV_PATH} not found, will continue without Katzkin data")

# --------------------------------------------------------------------
# 2. Parsing with Excel authority
# --------------------------------------------------------------------
def extract_design_number(name, description="", slug=""):
    """Extract design number from product name, description, or slug."""
    # Pattern: K/F/L followed by digits, dash, 2-4 digits (e.g., K1384-10, K1384-100, F1248-1000)

    # First try slug (most reliable source)
    if slug:
        slug_match = re.search(r"\b([KFL]\d{1,4}-\d{2,4})\b", slug, re.IGNORECASE)
        if slug_match:
            return slug_match.group(1).upper()

    # Then try name and description
    combined_text = f"{name} {description}"
    design_match = re.search(r"\b([KFL]\d{1,4}-\d{2,4})\b", combined_text, re.IGNORECASE)
    if design_match:
        return design_match.group(1).upper()

    return ""

def parse_product_name(name):
    """Extract year, make, model, and design from product name"""
    normalized_name = clean_text(name)

    year = ""
    make = ""
    model = ""
    design_name = ""

    # Year detection (supports ranges like 2014-2021)
    year_match = re.search(r"(19|20)\d{2}(?:\s*-\s*(?:19|20)\d{2})?", normalized_name)
    if year_match:
        year = clean_text(year_match.group(0))

    # Design extraction (Custom/Factory Design strings)
    design_match = re.search(
        r"(Custom Design\s+[A-Z0-9-]+|Factory Design\s+[A-Z0-9-]+)",
        normalized_name,
        re.IGNORECASE
    )
    if design_match:
        design_name = clean_text(design_match.group(0))

    # Extract make and model from pattern: "Design for Make Model Trim Year"
    # Example: "Custom Design K9 for Landrover Freelander 1999"
    for_match = re.search(r'\bfor\s+(.+?)(?:\s+(?:19|20)\d{2}|$)', normalized_name, re.IGNORECASE)
    if for_match:
        vehicle_part = for_match.group(1).strip()
        # Remove design name if it's in this part
        if design_name:
            vehicle_part = vehicle_part.replace(design_name, '').strip()

        # Split into words
        words = vehicle_part.split()
        if len(words) >= 2:
            make = words[0]
            model = ' '.join(words[1:])

    return year, make, model, design_name


# --------------------------------------------------------------------
# 3. Scrape all pages
# --------------------------------------------------------------------
products = []
unmatched = []
offset = 0

while True:
    params = API_DEFAULT_PARAMS.copy()
    params["offset"] = offset
    print(f"Fetching products offset {offset}...")

    response = requests.get(PRODUCTS_API_URL, params=params, headers=REQUEST_HEADERS, timeout=30)
    response.raise_for_status()
    payload = response.json()

    items = payload.get("products", [])
    total = payload.get("total")
    print(f"  Retrieved {len(items)} items (total reported: {total})")

    if not items:
        break

    # Process items and fetch trim from variants API
    for idx, item in enumerate(items):
        product_id = item.get("_id")

        name = item.get("name", "").strip()
        description = item.get("description", "").strip()
        slug = item.get("slug", "").strip()
        amount = item.get("amount")
        currency = item.get("currency", "USD")
        price = ""
        if isinstance(amount, (int, float)):
            if currency and currency.upper() != "USD":
                price = f"{currency} {amount:.2f}"
            else:
                price = f"${amount:.2f}"
        elif amount:
            price = str(amount)

        image = fetch_image_url(item)
        link = build_product_url(item)

        year, make, model, design_name = parse_product_name(name)
        design_number = extract_design_number(name, description, slug)

        # Extract trim from variants field if available (from GHL bulk upload data)
        trim = ""
        variants = item.get("variants", [])
        for variant in variants:
            variant_name = variant.get("name", "").lower()
            if variant_name == "trim":
                options = variant.get("options", [])
                if options and len(options) > 0:
                    option_value = options[0].get("name", "").strip()
                    # Remove design number from trim if present
                    option_value = re.sub(r'\s+[KFL]\d{4,7}$', '', option_value)
                    option_value = re.sub(r'\s+[KFL]\d{1,4}-\d{2,4}$', '', option_value).strip()
                    trim = option_value
                break

        # Override trim with Katzkin data if available
        if design_number and design_number in KATZKIN_TRIM_MAP:
            trim = KATZKIN_TRIM_MAP[design_number]

        # Progress indicator
        if (idx + 1) % 100 == 0:
            print(f"    Processed {idx + 1}/{len(items)} products...")

        record = {
            "year": year,
            "make": make,
            "model": model,
            "trim": trim,
            "name": name,
            "price": price,
            "image": image,
            "url": link
        }
        if design_name and design_name != trim:
            record["design"] = design_name
        if design_number:
            record["designNumber"] = design_number
        products.append(record)

        if not make:
            unmatched.append(record)

    offset += API_PAGE_SIZE

    # Stop only when no more items are returned
    if len(items) < API_PAGE_SIZE:
        break

    time.sleep(0.1)  # Small delay to avoid rate limiting

# --------------------------------------------------------------------
# 4. Save outputs
# --------------------------------------------------------------------
with open(PRODUCTS_JSON, "w", encoding="utf-8") as f:
    json.dump(products, f, indent=2, ensure_ascii=False)

with open(UNMATCHED_JSON, "w", encoding="utf-8") as f:
    json.dump(unmatched, f, indent=2, ensure_ascii=False)

def expand_year_range(year_string):
    """
    Expand a year range string into individual years.
    Examples:
        "2021-2025" -> [2021, 2022, 2023, 2024, 2025]
        "2023" -> [2023]
        "2018 - 2022" -> [2018, 2019, 2020, 2021, 2022]
    """
    if not year_string:
        return []

    # Clean the string
    cleaned = year_string.strip().replace(" ", "")

    # Check if it's a range
    if "-" in cleaned:
        parts = cleaned.split("-")
        if len(parts) == 2:
            try:
                start_year = int(parts[0])
                end_year = int(parts[1])
                # Return all years in the range (inclusive)
                return list(range(start_year, end_year + 1))
            except ValueError:
                # If parsing fails, return empty list
                return []

    # Single year
    try:
        return [int(cleaned)]
    except ValueError:
        return []

# Dropdown structures - expand year ranges to individual years
MakeByYear, MakeModel, MakeTrim = {}, {}, {}
for p in products:
    year_range = p["year"]
    mk, md, tr = p["make"], p["model"], p["trim"]

    if not year_range or not mk or not md:
        continue

    # Expand year range to individual years
    individual_years = expand_year_range(year_range)

    # Add this product's data to each individual year
    for year in individual_years:
        year_str = str(year)

        # MakeByYear
        MakeByYear.setdefault(year_str, [])
        if mk not in MakeByYear[year_str]:
            MakeByYear[year_str].append(mk)

        # MakeModel
        MakeModel.setdefault(year_str, {}).setdefault(mk, [])
        if md not in MakeModel[year_str][mk]:
            MakeModel[year_str][mk].append(md)

        # MakeTrim
        MakeTrim.setdefault(year_str, {}).setdefault(mk, {}).setdefault(md, [])
        if tr and tr not in MakeTrim[year_str][mk][md]:
            MakeTrim[year_str][mk][md].append(tr)

with open(DROPDOWN_DATA, "w", encoding="utf-8") as f:
    f.write("const MakeByYear = " + json.dumps(MakeByYear, indent=2) + ";\n\n")
    f.write("const MakeModel = " + json.dumps(MakeModel, indent=2) + ";\n\n")
    f.write("const MakeTrim = " + json.dumps(MakeTrim, indent=2) + ";\n")

print(f"Done. Scraped {len(products)} products, {len(unmatched)} unmatched.")
