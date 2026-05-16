---
date: 2026-05-16
topic: anonymizer-core
---

# Internal Data Anonymizer — Requirements

## Summary

A local web app (FastAPI + Svelte) that anonymizes tabular data through a guided column-by-column review workflow, with deterministic project-level mappings stored in SQLite, format-preserving fakes for product/retail data, and bidirectional reverse lookup.

---

## Problem Frame

Data consultants who work with client data can't share it publicly — not in portfolio pieces, demos, or when troubleshooting. The workarounds are bad: hand-built fake datasets that don't reflect real-world messiness, or manually anonymized data that's tedious to produce and error-prone to maintain across files.

The current process is manual: sort data so similar values group together, create a mapping by hand, apply replacements one by one. This works but doesn't scale, doesn't preserve statistical shape, and produces no reusable artifact. Every new client dataset starts from zero.

Generic anonymizers (Faker, Mimesis) produce output that's statistically useless and visibly fake — they don't understand product data structures like UPCs, GTINs, or retailer naming patterns.

---

## Key Flows

- F1. First-file anonymization
  - **Trigger:** User uploads a file into a project
  - **Steps:** Upload → tool scans columns and auto-suggests strategy per column → user confirms/overrides strategy column-by-column → tool generates proposed mappings → user reviews mappings (can regenerate, edit individually, or set bulk pattern rules) → user approves → tool applies and outputs anonymized file
  - **Outcome:** Anonymized file in chosen format; mappings persisted to project database

- F2. Subsequent-file anonymization
  - **Trigger:** User uploads another file into an existing project
  - **Steps:** Upload → tool auto-applies existing mappings for known values → tool scans for NEW values only → user reviews only new mappings → approve → output
  - **Outcome:** Anonymized file with consistent mappings across all project files

- F3. Reverse lookup
  - **Trigger:** User sees an anonymized value and needs to trace it back
  - **Steps:** Search bar (paste/type anonymized value → see original) OR browse anonymized output in tool and click any cell to reveal original
  - **Outcome:** Operator confirms which original value maps to the anonymized one

---

## Requirements

**Project management**

- R1. Landing page shows a project dashboard listing all projects with name, creation date, and file count.
- R2. User can create, open, and delete projects from the dashboard.
- R3. Each project stores its mappings in a dedicated SQLite database file.
- R4. Projects are independent — mappings do not bleed across projects.

**File handling**

- R5. Accept input files in CSV, XLSX, JSON, and Parquet formats.
- R6. User chooses output format independently of input format (CSV, XLSX, JSON, Parquet).
- R7. File upload size is bounded by available RAM (pandas in-memory). No artificial limit needed for expected data sizes (hundreds to low thousands of rows).

**Column strategy assignment**

- R8. Tool auto-detects column types (names, numbers, IDs, dates, codes, etc.) and proposes a strategy for each column.
- R9. Available strategies: fake, jitter, format-preserve, hash, drop, passthrough.
- R10. User confirms or overrides the suggested strategy per column in a column-by-column flow.

**Mapping review and editing**

- R11. For each column with a generative strategy (fake, format-preserve), show all unique values with their proposed replacements.
- R12. User can regenerate all mappings for a column (fresh set of fakes).
- R13. User can edit any individual mapping by typing a custom replacement.
- R14. User can define bulk pattern rules (e.g., `[Adjective] [Noun] [4-digit number]`) applied to all values in a column.
- R15. When a subsequent file is uploaded to the same project, existing mappings auto-apply. Only new (unseen) values enter the review flow.

**Numeric preservation**

- R16. Numeric columns with jitter strategy preserve statistical distribution shape (mean, variance, skew, range).
- R17. Show a before/after histogram preview (sparkline-style inline chart) so the user can verify shape is preserved.
- R18. If the preview looks wrong, user can manually adjust jitter parameters (range, rounding, min/max preservation).
- R19. Null patterns preserved: if X% of rows are null, approximately X% of anonymized rows are null.

**Format-preserving fakes**

- R20. UPC/GTIN: generate codes of correct length with valid check digits. Mirror input data quality — if original has invalid check digits, fakes include invalid ones at the same rate.
- R21. Company/store names: draw from a curated pool of plausible business names, not generated strings like "Company_47831."
- R22. Phone numbers and emails: format-correct (valid area codes, real-looking email domains).
- R23. SKU/internal ID pattern-matching: analyze the structure of existing values (e.g., `ABC-1234-X`) and generate fakes following the same pattern.
- R24. Dirty-data fidelity: if the original column has X% invalid/malformed values, the anonymized column has approximately X% invalid/malformed fakes.

**Reverse lookup**

- R25. Search bar accessible from any screen: paste or type an anonymized value, see its original.
- R26. When viewing anonymized output in the tool, click any cell to reveal its original value.
- R27. Reverse lookup is available only to the operator (whoever runs the tool). No separate access control needed — local tool, localhost access.

**Determinism**

- R28. Within a project, the same input value always produces the same anonymized output across runs and files.
- R29. Different projects produce different mappings for the same input value.

---

## Acceptance Examples

- AE1. **Covers R15, R28.** Given a project with File A already anonymized (containing "Costco" → "Alpine Market 3847"), when File B is uploaded containing "Costco" in the same column, "Costco" auto-maps to "Alpine Market 3847" without user intervention.
- AE2. **Covers R20, R24.** Given a column of 100 UPCs where 8 have invalid check digits, when anonymized with format-preserve strategy, the output contains ~8 UPCs with invalid check digits and ~92 with valid ones.
- AE3. **Covers R16, R19.** Given a numeric column with mean=450, std=120, and 15% nulls, when anonymized with jitter strategy, the output has approximately the same mean, std, and 15% null rate.
- AE4. **Covers R23.** Given a SKU column with values like "WM-8842-A", "TG-1156-C", "CS-3301-B", when anonymized with format-preserve, output follows the pattern `[2 letters]-[4 digits]-[1 letter]`.

---

## Success Criteria

- The operator can anonymize a client CSV and produce output that looks plausible to a human reviewer without any visible connection to the original data.
- Anonymized output preserves join-ability across multiple files within a project.
- The tool is genuinely faster than the manual sort-and-replace workflow it replaces.
- The GitHub repo with README and worked example demonstrates product-building skill distinct from analytical portfolio pieces.
- One Lailara portfolio piece uses the tool's output and links back to the repo.

---

## Scope Boundaries

- Desktop app packaging (Electron/Tauri) — deferred to v2
- User accounts, authentication, or multi-user collaboration
- Database connections as input source
- Free-text anonymization (addresses, notes, comments fields)
- Differential privacy or mathematical privacy guarantees
- YAML/JSON config export as shareable "recipe" artifact
- Deployment to a hosted server — runs locally only
- Undo/version history within a project
- Transformation report / audit trail export
- Non-technical user onboarding or guided help

---

## Key Decisions

- **Column-by-column review over full-table overview:** Reduces cognitive load. User focuses on one column at a time, confirming strategy and reviewing mappings before moving to the next.
- **SQLite per project:** Enables efficient reverse lookup via query, simple backup (one file), and natural isolation between projects. Best practice for local tool with structured mapping data.
- **FastAPI + Svelte:** Python backend keeps data engine in Shawn's domain of expertise. Svelte frontend satisfies the "new territory / fun build" goal with lighter boilerplate than React.
- **Auto-apply existing mappings on subsequent files:** Preserves referential integrity across files with zero friction. Only new values require attention.
- **No auth:** Local tool, localhost only. Whoever can access the machine can use the tool.

---

## Dependencies / Assumptions

- Python 3.10+ (FastAPI, pandas, type hints)
- pandas for tabular data operations
- Svelte 5 (current stable) with SvelteKit or standalone
- SQLite via Python's built-in `sqlite3` module
- Faker library as the foundation for fake data generation, extended with custom product-data modules
- User has a modern browser for the Svelte frontend
- Data sizes remain in the hundreds-to-low-thousands row range (RAM-bounded is not a practical constraint)

---

## Outstanding Questions

### Deferred to Planning

- [Affects R8][Needs research] What heuristics should auto-detection use to classify column types? (Pattern analysis, value distributions, column name keywords?)
- [Affects R14][Technical] How should bulk pattern rules be specified in the UI? (Template syntax, example-based, regex?)
- [Affects R20][Needs research] What library or approach generates valid UPC/GTIN check digits in Python?
- [Affects R21][Technical] How large does the curated company/store name pool need to be for v1? (50? 200? 500?)
- [Affects R16][Technical] Which statistical method preserves distribution shape best for small datasets — jittering within bounds, or resampling from a fitted distribution?
