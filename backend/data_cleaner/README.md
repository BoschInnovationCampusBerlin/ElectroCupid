# Electro Cupid – BOM Cleaning Pipeline

## Project Goal
Standardize messy BOM (Bill of Materials) files (CSV, XLSX, PDF) into a clean format, ready for API use (e.g., Octopart). Handles multiple languages, typos, and missing data.

## Features
- Reads BOMs in CSV, XLSX, or PDF
- Standardizes column names (MPN, alternatives, description)
- Handles missing MPNs using alternatives or description
- Corrects typos in part numbers
- Translates descriptions to English
- Outputs a clean CSV ready for further processing

## Setup
1. **Clone the repo**
2. **Install dependencies:**
   ```bash
   pip install -r requirements.txt
   ```
   - For PDF support, you may need Java (for `tabula-py`).

## Usage
```bash
python bom_cleaner.py <input_file> [-o <output_file>]
```
- `<input_file>`: Path to your BOM file (csv, xlsx, or pdf)
- `-o <output_file>`: (Optional) Path to save the cleaned BOM (default: `cleaned_bom.csv`)

**Example:**
```bash
python bom_cleaner.py my_bom.xlsx -o output.csv
```

## Notes
- The script uses fuzzy matching to find the correct columns, even if headers are in different languages or have typos.
- Typos in part numbers are corrected using a dummy list (`KNOWN_PARTS`). Replace this with real data or integrate with Octopart for best results.
- Descriptions are translated to English using Google Translate API.
- For PDF extraction, results may vary depending on the table structure.

## Extending
- Add more known part numbers to `KNOWN_PARTS` in `bom_cleaner.py` for better typo correction.
- Integrate with Octopart API for real-time part validation and enrichment. 