# ⚡ Quick Workflow Summary

## Adding New Products (Complete Process)

**IMPORTANT: Always follow ALL steps in order!**

### ✅ Step 1: Add Products from Excel
```bash
python product_cli.py add-products new_products.xlsx
```

### ✅ Step 2: Fetch URLs from GHL ⚠️ REQUIRED!
```bash
python product_cli.py fetch-urls
```
**Why?** Products from Excel don't have URLs. This step searches GHL API by design number and adds the URLs.

### ✅ Step 3: Clean Trims
```bash
python product_cli.py clean-trims
```
**Why?** Removes design numbers and error codes from trim names.

### ✅ Step 4: Fill Missing Trims (if needed)
```bash
python product_cli.py fill-trims
```
**Why?** Fills any missing trim data from Excel/Katzkin sources.

### ✅ Step 5: Verify
```bash
python product_cli.py stats
```
**Check:**
- Without URL: 0 ✅
- Without trim: minimal ✅

### ✅ Step 6: Commit & Push
```bash
git add products.json
git commit -m "feat: add [X] new products

- Added [X] new products from Excel
- Fetched URLs from GHL API
- Cleaned trim data

🤖 Generated with [Claude Code](https://claude.com/claude-code)

Co-Authored-By: Claude <noreply@anthropic.com>"

git push
```

---

## Common Operations

### Check Product Stats
```bash
python product_cli.py stats
```

### Clean Trim Data
```bash
python product_cli.py clean-trims --dry-run  # Preview
python product_cli.py clean-trims            # Execute
```

### Fix Missing URLs
```bash
python product_cli.py fetch-urls
```

### Full Rescrape from GHL
```bash
cd scrapers && python ghl_scraper.py
cd .. && python product_cli.py clean-trims && python product_cli.py fill-trims
```

---

## 📚 Documentation

- **[Complete SOP](SOP.md)** - Detailed procedures, troubleshooting, and reference
- **[README](README.md)** - File structure and overview
- **This file** - Quick reference for daily tasks

---

## ⚠️ Remember

1. **ALWAYS run `fetch-urls` after adding products from Excel**
2. **ALWAYS clean trims after rescraping from GHL**
3. **ALWAYS verify with `stats` before committing**
4. **ALWAYS commit and push after data changes**
