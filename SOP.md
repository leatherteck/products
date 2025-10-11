# Standard Operating Procedure (SOP)
## LeatherTek Product Management

---

## Table of Contents
1. [Adding New Products](#1-adding-new-products)
2. [Updating Existing Products](#2-updating-existing-products)
3. [Scraping Products from GHL](#3-scraping-products-from-ghl)
4. [Data Maintenance](#4-data-maintenance)
5. [Troubleshooting](#5-troubleshooting)

---

## 1. Adding New Products

### Overview
When new products are uploaded to GHL store, they need to be added to products.json with proper URLs and clean trim data.

### Prerequisites
- New products uploaded to GHL store
- Excel file with product data (format: Design Name, Make, Model, Trim, Year, Description, Design Number, Image URL)

### Step-by-Step Process

#### Step 1: Prepare Excel File
Ensure your Excel file (`new_products.xlsx`) has the following structure:
- **Column 0**: Design Name (e.g., "FACTORY DESIGN F1")
- **Column 1**: Make (e.g., "Honda")
- **Column 2**: Model (e.g., "Accord")
- **Column 3**: Trim (e.g., "LX / SPORT / EX / HYBRID")
- **Column 4**: Year (e.g., "2018-2022")
- **Column 5**: Description
- **Column 6**: Design Number (e.g., "F1282-100")
- **Column 7**: Image URL
- **No headers** - data starts at row 0

#### Step 2: Add Products to JSON
```bash
python product_cli.py add-products new_products.xlsx
```

**Expected Output:**
```
Added 77 new products

=== Product Statistics ===
Total products: 22163
Without URL: 77  # <-- These need URLs!
```

#### Step 3: Fetch URLs from GHL
**IMPORTANT:** Products added from Excel don't have URLs. You MUST fetch them from GHL:

```bash
python product_cli.py fetch-urls
```

**This command will:**
1. Find all products without URLs
2. Search GHL API by design number
3. Match products and update URLs
4. Save to products.json

**Expected Output:**
```
Found 77 products without URLs
Fetching all products from GHL API...
  Found: F1282-100 -> https://leatherteck.com/item-details/product/68e8487be22f98535839aafa
  ...
Updated 77 products with URLs
Still missing URLs: 0
```

#### Step 4: Clean Trim Data
Remove any design numbers that got added to trim names:

```bash
# Preview what will be cleaned
python product_cli.py clean-trims --dry-run

# Clean the trims
python product_cli.py clean-trims
```

#### Step 5: Fill Missing Trims (if needed)
If any products are missing trim data:

```bash
python product_cli.py fill-trims
```

#### Step 6: Verify Data
```bash
python product_cli.py stats
```

**Check:**
- ✅ Without URL: should be 0
- ✅ Without trim: should be minimal
- ✅ All design numbers present

#### Step 7: Commit and Push
```bash
git add products.json
git commit -m "feat: add [X] new products with [description]

- Added [X] new products from new_products.xlsx
- Fetched URLs from GHL API
- Cleaned trim data

🤖 Generated with [Claude Code](https://claude.com/claude-code)

Co-Authored-By: Claude <noreply@anthropic.com>"

git push
```

---

## 2. Updating Existing Products

### Clean Trim Data
If trims have design numbers or error codes:

```bash
python product_cli.py clean-trims --dry-run  # Preview
python product_cli.py clean-trims            # Execute
```

**Removes:**
- Design numbers: "STX K22" → "STX"
- Error codes: "BASE (Code Error)" → "BASE"
- Katzkin codes: "LX K1234-100" → "LX"

### Fill Missing Trims
```bash
python product_cli.py fill-trims              # All sources
python product_cli.py fill-trims --excel      # Excel only
python product_cli.py fill-trims --katzkin    # Katzkin only
```

### Fetch Missing URLs
If products are missing URLs:

```bash
python product_cli.py fetch-urls
```

---

## 3. Scraping Products from GHL

### Full Rescrape
When you need to get all products fresh from GHL:

```bash
cd scrapers
python ghl_scraper.py
```

**WARNING:** This will overwrite `products.json`!

**After rescraping, you MUST:**
1. Clean trims: `python product_cli.py clean-trims`
2. Fill missing trims: `python product_cli.py fill-trims`
3. Verify: `python product_cli.py stats`

### Scrape Katzkin Data
To get fresh trim data from Katzkin:

```bash
cd scrapers
python scrape_katzkin_from_excel.py
```

This creates/updates:
- `katzkin_from_excel.csv`
- `katzkin_from_excel.json`

---

## 4. Data Maintenance

### Daily Checks
```bash
python product_cli.py stats
```

Monitor:
- Products without URLs
- Products without trims
- Total product count

### Weekly Tasks
1. **Rescrape GHL** (if needed):
   ```bash
   cd scrapers && python ghl_scraper.py
   ```

2. **Clean and fill data**:
   ```bash
   python product_cli.py clean-trims
   python product_cli.py fill-trims
   ```

3. **Commit changes**:
   ```bash
   git add products.json
   git commit -m "update: weekly product data maintenance"
   git push
   ```

---

## 5. Troubleshooting

### Problem: Products added but no URLs

**Symptom:**
```
Without URL: 77
```

**Solution:**
```bash
python product_cli.py fetch-urls
```

The script will search GHL API by design number and update URLs.

---

### Problem: Trims have design numbers

**Symptom:**
```
Trim: "STX K22" or "BASE K2973-224 (Code Error)"
```

**Solution:**
```bash
python product_cli.py clean-trims
```

---

### Problem: Missing trims

**Symptom:**
```
Without trim: 2492
```

**Solution:**
```bash
python product_cli.py fill-trims
```

This will match by design number from Excel and Katzkin data.

---

### Problem: URL fetch not finding products

**Symptom:**
```
Found 0 URLs
Still missing URLs: 77
```

**Possible Causes:**
1. Products not uploaded to GHL yet
2. Design numbers don't match
3. GHL API issue

**Solutions:**
1. Verify products are in GHL store
2. Check design numbers match exactly (case-sensitive)
3. Try re-running after a few minutes

---

### Problem: Excel file format error

**Symptom:**
```
Error reading Excel file
```

**Solution:**
Ensure Excel file has:
- No headers (data starts row 0)
- 8 columns in correct order
- No empty rows at top

---

## Quick Reference Commands

```bash
# Show stats
python product_cli.py stats

# Add new products (requires fetch-urls after!)
python product_cli.py add-products new_products.xlsx
python product_cli.py fetch-urls

# Clean data
python product_cli.py clean-trims
python product_cli.py fill-trims

# Full rescrape
cd scrapers && python ghl_scraper.py
cd .. && python product_cli.py clean-trims && python product_cli.py fill-trims

# Commit
git add products.json
git commit -m "update: [description]"
git push
```

---

## File Locations

- **Main CLI**: `product_cli.py`
- **Products Database**: `products.json`
- **Dropdown Data**: `dropdown_data.js`
- **GHL Scraper**: `scrapers/ghl_scraper.py`
- **Katzkin Scraper**: `scrapers/scrape_katzkin_from_excel.py`
- **Excel Data**: `data/current.xlsx`
- **Katzkin CSV**: `katzkin_from_excel.csv`

---

## Notes

- **Always run `fetch-urls` after adding products from Excel**
- **Always clean trims after rescraping from GHL**
- **Commit and push after any data changes**
- **Use `--dry-run` to preview changes before executing**
