# LeatherTek Product Management

## 📋 Standard Operating Procedure (SOP)

**👉 [Read the complete SOP here](SOP.md)**

The SOP covers:
- ✅ Adding new products (with URL fetching!)
- ✅ Updating existing products
- ✅ Data maintenance
- ✅ Troubleshooting common issues

## Quick Start

All product operations are centralized in `product_cli.py`:

```bash
# Show product statistics
python product_cli.py stats

# Add new products (IMPORTANT: must fetch URLs after!)
python product_cli.py add-products new_products.xlsx
python product_cli.py fetch-urls  # <-- Don't forget this!

# Clean design numbers from trims
python product_cli.py clean-trims --dry-run  # Preview first
python product_cli.py clean-trims

# Fill missing trims
python product_cli.py fill-trims              # From all sources
python product_cli.py fill-trims --excel      # From Excel only
python product_cli.py fill-trims --katzkin    # From Katzkin only

# Fetch URLs for products without URLs
python product_cli.py fetch-urls
```

## File Structure

```
LeatherTek/
├── product_cli.py           # Main CLI tool - use this for all operations
├── products.json            # Product database (do not edit manually)
├── dropdown_data.js         # Dropdown data for website
│
├── scrapers/
│   ├── ghl_scraper.py       # Fetch products from GHL store
│   └── scrape_katzkin_from_excel.py
│
├── data/
│   ├── current.xlsx         # Current product data
│   └── katzkin_from_excel.csv
│
├── ghl-sections/            # GHL page sections
├── html_pages/              # HTML page templates
└── images/                  # Product images
```

## Workflow

### 1. Scrape Latest Products from GHL
```bash
cd scrapers
python ghl_scraper.py
```

### 2. Clean and Fill Data
```bash
# Check what needs cleaning
python product_cli.py stats

# Clean trims (preview first)
python product_cli.py clean-trims --dry-run
python product_cli.py clean-trims

# Fill missing trims
python product_cli.py fill-trims
```

### 3. Add New Products
```bash
# Add from Excel file
python product_cli.py add-products new_products.xlsx
```

### 4. Commit Changes
```bash
git add products.json
git commit -m "update: product data"
git push
```

## Data Sources

- **GHL Store API**: Primary source for all products
- **Excel (data/current.xlsx)**: Trim data for matching by design number
- **Katzkin CSV**: Additional trim data from Katzkin website

## Key Scripts

- `product_cli.py` - **Use this for everything**
- `scrapers/ghl_scraper.py` - Fetch from GHL API
- Individual `check_*.py`, `clean_*.py` files are deprecated (functionality moved to CLI)
