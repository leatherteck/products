import pandas as pd
import re
from pathlib import Path

# File paths
EXCEL_PATH = "EM Upholstery Technology.xlsx"
OUTPUT_CSV = "products_bulk_upload_with_trim.csv"

def clean_text(value):
    """Clean and normalize text values."""
    if pd.isna(value) or value is None:
        return ""
    text = str(value).strip()
    # Remove extra whitespace but preserve newlines for descriptions
    return text

def create_product_title(row):
    """Generate product title from Excel data."""
    # Format: [Title Design] for [Car Brand] [Car Unit] [Trim] [Year]
    parts = []

    title_design = clean_text(row.get('Title Design', ''))
    car_brand = clean_text(row.get('Car Brand', ''))
    car_unit = clean_text(row.get('Car Unit', ''))
    trim = clean_text(row.get('Trim', ''))
    year = clean_text(row.get('Year', ''))

    # Build title (WITHOUT design number)
    if title_design:
        parts.append(title_design)

    if parts:
        parts.append('for')

    if car_brand:
        parts.append(car_brand)

    # Only add car_unit if it's not the unwanted text
    unwanted_texts = ["DON'T KNOW", "DON'T SEE", "MY OPTIONS", "DON'T KNOW/DON'T SEE MY OPTIONS"]

    if car_unit:
        # Check if car_unit contains any unwanted text
        if not any(unwanted.upper() in car_unit.upper() for unwanted in unwanted_texts):
            parts.append(car_unit)

    # Only add trim if it's not the unwanted text
    if trim:
        # Check if trim contains any unwanted text
        if not any(unwanted.upper() in trim.upper() for unwanted in unwanted_texts):
            parts.append(trim)

    if year:
        parts.append(year)

    return ' '.join(parts)

def create_handle(row, index):
    """Create a unique handle for the product."""
    # Create unique handle from design number + car brand + car unit + year + index
    design_number = clean_text(row.get('Design Number', ''))
    car_brand = clean_text(row.get('Car Brand', ''))
    car_unit = clean_text(row.get('Car Unit', ''))
    year = clean_text(row.get('Year', ''))
    title_design = clean_text(row.get('Title Design', ''))

    parts = []

    if design_number:
        # Clean design number
        clean_dn = re.sub(r'[^a-zA-Z0-9-]', '-', design_number.lower())
        clean_dn = re.sub(r'-+', '-', clean_dn).strip('-')
        parts.append(clean_dn)

    if car_brand:
        clean_brand = re.sub(r'[^a-zA-Z0-9-]', '-', car_brand.lower())
        clean_brand = re.sub(r'-+', '-', clean_brand).strip('-')
        parts.append(clean_brand)

    if car_unit:
        clean_unit = re.sub(r'[^a-zA-Z0-9-]', '-', car_unit.lower())
        clean_unit = re.sub(r'-+', '-', clean_unit).strip('-')
        # Skip unwanted text in handle
        if not any(unwanted.upper() in car_unit.upper() for unwanted in ["DON'T KNOW", "DON'T SEE", "MY OPTIONS"]):
            parts.append(clean_unit)

    if year:
        clean_year = re.sub(r'[^a-zA-Z0-9-]', '-', year.lower())
        clean_year = re.sub(r'-+', '-', clean_year).strip('-')
        parts.append(clean_year)

    # Add title design to differentiate (extract just K1, K2, F1, etc.)
    if title_design:
        design_code = re.search(r'(K\d+|F\d+)', title_design, re.IGNORECASE)
        if design_code:
            parts.append(design_code.group(1).lower())

    # Add index as final unique identifier
    parts.append(str(index))

    if parts:
        return '-'.join(parts)

    return f"product-{index + 1}"

def format_description_html(description, design_number=""):
    """Convert description text to simple HTML with design number at the beginning."""
    html_parts = []

    # Add design number at the beginning if provided
    if design_number:
        html_parts.append(f'<p><strong>Design Number: {design_number}</strong></p>')

    if not description:
        return ''.join(html_parts) if html_parts else ""

    # Split by newlines and create HTML list or paragraphs
    lines = [line.strip() for line in description.split('\n') if line.strip()]

    if len(lines) > 1:
        # Create bullet list for multi-line descriptions
        html_parts.append('<ul>')
        for line in lines:
            html_parts.append(f'<li>{line}</li>')
        html_parts.append('</ul>')
    elif len(lines) == 1:
        html_parts.append(f'<p>{lines[0]}</p>')

    return ''.join(html_parts)

def extract_excel_to_csv():
    """Main extraction function."""
    print(f"Reading Excel file: {EXCEL_PATH}")

    # Read Excel file
    df = pd.read_excel(EXCEL_PATH)

    print(f"Total rows in Excel: {len(df)}")
    print(f"Columns: {df.columns.tolist()}")

    # Prepare CSV data structure matching sample format
    csv_data = []

    for index, row in df.iterrows():
        # Extract all fields
        title_design = clean_text(row.get('Title Design', ''))
        car_brand = clean_text(row.get('Car Brand', ''))
        car_unit_raw = clean_text(row.get('Car Unit', ''))
        trim_raw = clean_text(row.get('Trim', ''))
        year = clean_text(row.get('Year', ''))
        design_description = clean_text(row.get('Design Description', ''))
        design_number = clean_text(row.get('Design Number', ''))
        image_link = clean_text(row.get('Image Link', ''))

        # Set default values if empty
        car_unit = car_unit_raw if car_unit_raw else "DON'T KNOW/DON'T SEE MY OPTIONS"
        trim = trim_raw if trim_raw else "DON'T KNOW/DON'T SEE MY OPTIONS"

        # Skip rows with missing essential data (blank rows)
        if not title_design or not car_brand or not year:
            continue

        # Generate fields
        handle = create_handle(row, index)
        title = create_product_title(row)
        body_html = format_description_html(design_description, design_number)

        # Skip if title is empty (filtered out)
        if not title:
            continue

        # Create product row
        product_row = {
            'Handle': handle,
            'Title': title,
            'Body (HTML)': body_html,
            'Included in Online Store': 'TRUE',
            'Image Src': image_link,
            'Option1 Name': 'Make',
            'Option1 Value': car_brand,
            'Option2 Name': 'Model',
            'Option2 Value': car_unit,
            'Option3 Name': 'Trim',
            'Option3 Value': trim,
            'Variant Price': '1895.00',  # Default price, can be adjusted
            'Variant Compare At Price': '',
            'Track Inventory': 'FALSE',
            'Allow Out of Stock Purchases': 'TRUE',
            'Available Quantity': '',
            'SKU': design_number,
            'Weight Value': '',
            'Weight Unit': '',
            'Dimension Length': '',
            'Dimension Width': '',
            'Dimension Height': '',
            'Dimension Unit': '',
            'Product Label Enable': 'FALSE',
            'Label Title': '',
            'Label Start Date': '',
            'Label End Date': '',
            'SEO Title': title,
            'SEO Description': design_description[:160] if design_description else title  # SEO desc limit
        }

        csv_data.append(product_row)

        # Print progress every 1000 rows
        if (index + 1) % 1000 == 0:
            print(f"Processed {index + 1} rows...")

    # Create DataFrame and save to CSV
    output_df = pd.DataFrame(csv_data)

    print(f"\nSaving to CSV: {OUTPUT_CSV}")
    output_df.to_csv(OUTPUT_CSV, index=False, encoding='utf-8')

    print(f"Successfully created CSV with {len(csv_data)} products")
    print(f"File saved: {OUTPUT_CSV}")

    # Summary
    print("\n=== SUMMARY ===")
    print(f"Total products exported: {len(csv_data)}")
    print(f"Products with images: {sum(1 for row in csv_data if row['Image Src'])}")
    print(f"Products with SKU: {sum(1 for row in csv_data if row['SKU'])}")
    print(f"Unique brands: {len(set(row['Option2 Value'] for row in csv_data if row['Option2 Value']))}")
    print(f"Unique models: {len(set(row['Option3 Value'] for row in csv_data if row['Option3 Value']))}")

if __name__ == "__main__":
    extract_excel_to_csv()
