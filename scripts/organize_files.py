import os
import shutil

# Define folder structure
folders = {
    'scripts': [
        'check_challenger.py',
        'check_challenger_json.py',
        'check_empty_model.py',
        'check_handles.py',
        'compare_excel_json.py',
        'convert_to_shopify.py',
        'extract_excel_to_csv.py',
        'scraper.py',
        'test_katzkin_design.py',
        'update_image_urls.py',
        'update_image_urls_by_sku.py',
        'update_padding.py',
        'organize_files.py'  # Move this script too after running
    ],
    'scrapers': [
        'scrape_katzkin_vehicles.py'
    ],
    'html_pages': [
        'comparison.html',
        'comparison_funnel.html',
        'custom-video-player.html',
        'dropdown_complete.html',
        'funnel_lets-get-you-leather.html',
        'ghl-full-funnel-compiled.html',
        'ghl-video.html',
        'Katzkin.html',
        'katzkin_design_response.html',
        'video-with-thumbnail.html'
    ],
    'data': [
        'CAR Image API.xlsx',
        'current.xlsx',
        'EM Upholstery Technology.xlsx',
        'katzkin_vehicles.csv',
        'katzkin_vehicles.json',
        'matched_products_report.csv',
        'products.json',
        'products_bulk_upload_final.csv',
        'products_bulk_upload_with_trim.csv',
        'sample.csv',
        'shopify.csv',
        'shopify_products_upload.csv',
        'shopify_products_upload_with_direct_urls.csv',
        'unmatched.json'
    ]
}

# Create folders
for folder in folders.keys():
    os.makedirs(folder, exist_ok=True)
    print(f"Created folder: {folder}")

# Move files
for folder, files in folders.items():
    for file in files:
        if os.path.exists(file):
            dest = os.path.join(folder, file)
            shutil.move(file, dest)
            print(f"Moved: {file} -> {folder}/")
        else:
            print(f"[SKIP] File not found: {file}")

print("\n[OK] File organization complete!")
print("\nFolder structure:")
print("  scripts/      - Utility Python scripts")
print("  scrapers/     - Web scraping scripts (scrape_katzkin_vehicles.py)")
print("  html_pages/   - HTML templates and pages")
print("  data/         - CSV, JSON, Excel data files")
