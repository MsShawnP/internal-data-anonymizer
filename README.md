# Data Anonymizer

A local web application that anonymizes tabular data through a guided column-by-column review workflow. Deterministic project-level mappings in SQLite, format-preserving fakes for product and retail data, and bidirectional reverse lookup.

## What it does

Given a CSV, XLSX, JSON, or Parquet file:

1. **Scans** each column and classifies it (email, phone, UPC/GTIN, name, date, numeric, etc.)
2. **Proposes** an anonymization strategy per column (fake, jitter, format-preserve, hash, drop, passthrough)
3. **Lets you review** and override each strategy in a step-by-step UI
4. **Generates** deterministic replacement values — same input always produces the same output within a project
5. **Exports** the anonymized file in your choice of format
6. **Provides reverse lookup** so the operator can trace any anonymized value back to the original

Mappings persist at the project level. Upload a second file to the same project and previously-seen values get the same anonymized replacements automatically.

## Setup

Requires Python 3.10+ and Node.js 18+.

```bash
# Clone and install
git clone <repo-url> && cd internal-data-anonymizer
pip install -r backend/requirements.txt
cd frontend && npm install && cd ..

# Start dev servers (backend on :8000, frontend on :5173)
powershell scripts/dev.ps1
# Or manually:
# Terminal 1: cd backend && python -m uvicorn app.main:app --reload --port 8000
# Terminal 2: cd frontend && npm run dev
```

Open http://localhost:5173 in your browser.

## Worked example

Using the included test data (`test-data/sample-retail.csv`) — 10 rows of retail transaction data with customer names, emails, phone numbers, product names, UPC codes, prices, quantities, order dates, and zip codes.

### 1. Create a project

From the dashboard, type a project name and click **Create Project**.

### 2. Upload a file

Click **Upload File**, select `test-data/sample-retail.csv`, click **Upload & Analyze**.

The system detects column types:

| Column | Detected type | Suggested strategy |
|--------|--------------|-------------------|
| customer_name | name | fake |
| email | email | fake |
| phone | phone | fake |
| product_name | name | fake |
| upc | upc_gtin | format-preserve |
| price | numeric | jitter |
| quantity | numeric | jitter |
| order_date | date | jitter |
| zip_code | numeric | jitter |

### 3. Review strategies

Step through each column. The UI shows data type, unique count, null rate, sample values, and a strategy dropdown. Confirm each or override as needed.

### 4. Review mappings

After confirming all strategies, click **Generate Mappings**. For each column:
- **fake** columns show an original → anonymized mapping table. Edit individual values or regenerate all.
- **jitter** columns show a before/after histogram comparing the original and jittered distributions.
- **format-preserve** columns generate values matching the structural pattern (e.g., valid UPC check digits).

Approve each column's mappings, or use the **Pattern Rule Editor** to apply bulk templates.

### 5. Export

Choose output format (CSV, XLSX, JSON, or Parquet) and download.

### 6. Reverse lookup

From the project page, paste any anonymized value into the search bar. The system returns the original value, column name, and source file.

## Architecture

```
backend/
  app/
    main.py              FastAPI entry point
    db.py                SQLite connection management (root + per-project)
    routers/             API endpoints (projects, upload, columns, mappings, export)
    services/
      detector.py        Column type classification
      engine.py          Deterministic fake generation (SHA-256 seeded)
      jitter.py          Rank-preserving numeric perturbation
      ingest.py          Multi-format file reader
      providers/         Custom Faker providers (retail, identifiers, patterns)
frontend/
  src/
    routes/              SvelteKit pages (dashboard, project, upload, review, export, lookup)
    lib/components/      Reusable UI (ColumnCard, MappingTable, PatternRuleEditor, Histogram, SearchBar)
    lib/stores/          Svelte 5 reactive stores
```

### Key design choices

- **Two-tier SQLite**: Root `app.db` for the project list; per-project `mappings.db` files for isolation and easy deletion.
- **Deterministic seeding**: `SHA-256(project_salt + column_name + original_value)` seeds Faker. Stored mappings are authoritative after approval.
- **String-first ingestion**: All files read as `dtype=str` to preserve leading zeros in identifiers (UPCs, GTINs, zip codes). Type detection happens post-read.
- **No server-side rendering**: Local tool — SvelteKit in SPA/static mode with Vite proxy to FastAPI.

## Supported formats

| Format | Read | Write |
|--------|------|-------|
| CSV | Yes | Yes |
| Excel (.xlsx) | Yes | Yes |
| JSON | Yes | Yes |
| Parquet | Yes | Yes |

## Limitations (v1)

- No free-text anonymization (notes, comments, addresses)
- No differential privacy guarantees
- No database connections — file-based only
- No desktop packaging — runs as a local web server
- No multi-user access control
