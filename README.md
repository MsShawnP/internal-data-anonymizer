# Data Anonymizer

A local web application that turns sensitive tabular data into safe, realistic test data — deterministic, format-preserving, and fully reversible by the operator.

## What it does

Given a CSV, XLSX, JSON, or Parquet file, the app:

1. **Scans** each column and classifies it (email, phone, UPC/GTIN, name, date, numeric, etc.)
2. **Proposes** an anonymization strategy per column (fake, jitter, format-preserve, hash, drop, passthrough)
3. **Lets you review** and override each strategy in a step-by-step UI
4. **Generates** deterministic replacement values — same input always produces the same output within a project
5. **Exports** the anonymized file in your choice of format (CSV, XLSX, JSON, or Parquet)
6. **Provides reverse lookup** so the operator can trace any anonymized value back to the original

Mappings persist at the project level. Upload a second file to the same project and previously-seen values get the same anonymized replacements automatically — so joins between files still work after anonymization.

## Why it matters

Sharing real operational data — customer names, pricing, product identifiers — with vendors, contractors, demo audiences, or cloud tools is a data-governance liability. Hand-scrubbing spreadsheets is slow and error-prone, and naive masking breaks the data: identifiers stop validating, distributions flatten, and files no longer join.

This tool solves the parts that make anonymization genuinely hard:

- **Deterministic mappings** keep relationships intact across files and repeat exports
- **Format-preserving fakes** generate values that still pass downstream validation (e.g., UPCs with valid check digits)
- **Rank-preserving jitter** keeps numeric distributions analytically useful
- **Reverse lookup** preserves traceability for the operator without exposing originals to recipients
- **Everything runs locally** — no data leaves your machine

## Quick start

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

Open http://localhost:5173, create a project, and upload the included sample (`test-data/sample-retail.csv` — 10 rows of retail transactions with names, emails, phones, UPCs, prices, and dates). The app detects each column type, walks you through strategy review and mapping approval, then exports the anonymized file. Paste any anonymized value into the project search bar to reverse-look-up the original.

## Tech stack

- **Backend:** Python, FastAPI, SQLite, Faker (custom retail/identifier providers)
- **Frontend:** SvelteKit (Svelte 5, SPA/static mode), Vite
- **Formats:** CSV, XLSX, JSON, and Parquet — read and write

## Project structure

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

- **Two-tier SQLite:** root `app.db` for the project list; per-project `mappings.db` files for isolation and easy deletion
- **Deterministic seeding:** `SHA-256(project_salt + column_name + original_value)` seeds Faker; stored mappings are authoritative after approval
- **String-first ingestion:** all files read as `dtype=str` to preserve leading zeros in identifiers (UPCs, GTINs, zip codes); type detection happens post-read

## Limitations (v1)

- No free-text anonymization (notes, comments, addresses)
- No differential privacy guarantees
- No database connections — file-based only
- No desktop packaging — runs as a local web server
- No multi-user access control

## License

MIT — see [LICENSE](LICENSE).
