# internal-data-anonymizer — Current Work Plan

The current arc of work. Updated when the arc changes, not every
session. For session-by-session state, see HANDOFF.md.

---

## Goal

Build a web-based data anonymization tool that scans tabular files, proposes
deterministic value mappings per column, lets the user review/edit mappings in
a UI, applies them, and provides reverse lookup — with project-level persistence
so mappings carry across files.

## Why this arc, why now

Portfolio diversification — shifting from purely analytical pieces to a
product-building demonstration. Also scratches a real consulting itch:
hand-anonymizing client data is tedious and error-prone.

## Business question this arc answers

Can I ship a polished, publicly visible tool that demonstrates product
engineering skill while also being genuinely useful in my consulting practice?

## Scope (from /clarify)

**In:**
- Web app (local, browser-based UI)
- Input: CSV, XLSX, JSON, Parquet
- Output: user's choice of format
- Workflow: scan → propose mapping → user reviews/edits → apply
- Deterministic mappings within a project (same input = same output across files)
- Numeric columns preserve statistical shape (mean, variance, skew)
- Format-preserving fakes (UPCs, GTINs, phone numbers, etc.) that mirror
  input data quality — valid originals get valid fakes, dirty originals get dirty fakes
- Reverse lookup: operator can trace any anonymized value back to original
- Project concept: mappings persist across multiple files within a project
- Polished GitHub repo with worked example

**Out (v1):**
- Desktop app packaging (v2 concern)
- Database connections
- Free-text anonymization (notes, comments, addresses)
- Differential privacy guarantees
- GUI for non-technical users (operator is the user for v1)
- Image, PDF, or unstructured data

## Tasks

All implementation units from `docs/plans/2026-05-16-001-feat-data-anonymizer-plan.md`:

- [x] U1: Project scaffolding — FastAPI + SvelteKit monorepo with SQLite
- [x] U2: Project dashboard — CRUD endpoints and Svelte dashboard UI
- [x] U3: File upload and column detection engine
- [x] U4: Strategy review UI — column-by-column confirmation flow
- [x] U5: Anonymization engine with custom Faker providers
- [x] U6: Rank-preserving numeric jitter with histogram preview
- [x] U7: Mapping review and edit UI (MappingTable, PatternRuleEditor)
- [x] U8: Apply mappings and multi-format export
- [x] U9: Reverse lookup (SearchBar, click-to-reveal in DataPreview)
- [x] U10: Multi-file mapping reuse

## Remaining before ship

- [x] End-to-end browser testing of full flow
- [x] README with worked example
- ~~Portfolio piece on Lailara site~~ (skipped — separate concern)

## Definition of done for this arc

- [ ] Tool accepts CSV/XLSX/JSON/Parquet and outputs in user-chosen format
- [ ] Web UI shows proposed mappings and allows editing before apply
- [ ] Deterministic: same input + same project = same output across runs/files
- [ ] Numeric columns preserve distribution shape visually and statistically
- [ ] Format-preserving fakes for structured identifiers (UPC, GTIN, phone, ZIP)
- [ ] Dirty-data fidelity: invalid originals produce invalid fakes at same rate
- [ ] Reverse lookup available in UI for the operator
- [ ] Project-level mapping persistence
- [x] Public GitHub repo with README and worked example
- ~~One portfolio piece on Lailara site using the tool's output~~ (deferred)

---

## Current Arc: Improvement pass (2026-05-22)

**Goal:** Fix correctness bugs, strengthen anonymization, and improve code quality across all 11 findings from the /improve audit.

**Why this arc, why now:** User lost track of the project and wants confidence it works correctly. Audit found 2 critical bugs (jitter export leaks real data, dtype inference crash), plus anonymization weaknesses and code quality issues.

**Tasks:**
- [x] 1. Fix jitter export — compute jitter at export time so jitter-strategy columns actually get anonymized
- [x] 2. Fix `_infer_dtype` crash on mixed-type numeric columns (NaN → int cast)
- [x] 3. Include column name in hash input to prevent cross-column matching
- [x] 4. Fix null_rate always 0.0 for CSV/XLSX (keep_default_na=False masks blanks)
- [x] 5. Protect integer jitter from rank-breaking ties after rounding
- [x] 6. Escape LIKE wildcards in reverse lookup
- [x] 7. Use usecols in read_file when only one column needed
- [x] 8. Wrap profile_columns in asyncio.to_thread
- [x] 9. Filter mappings to file's columns at export
- [x] 10. Replace raw fetch() calls in review page with api.ts client
- [x] 11. Document npm audit deferrals (no code change, just tracking)

**Out of scope:** npm major version upgrades (SvelteKit/Vite), new features

**Definition of done:** All 81+ tests pass, each fix verified, no regressions

---

## Arc history

When an arc completes, archive its goal, completion date, and outcome
here. Then start a new arc above. Provides continuity without bloating
the active plan.

### 2026-05-22 — Improvement pass
- **Trigger:** User-initiated (`/improve`) — lost track of project, wanted confidence it works correctly
- **What was reviewed:** Full audit: code quality, security, correctness, tests, dependencies, workflow files
- **What was fixed:**
  - CRITICAL: Jitter columns now actually anonymized at export (were silently passing through real data)
  - CRITICAL: `_infer_dtype` no longer crashes on mixed-type numeric columns
  - Hash strategy now includes column name in hash input (prevents cross-column value matching)
  - null_rate now correctly counts empty strings as nulls for CSV/XLSX files
  - Integer jitter resolves ties after rounding to preserve rank order
  - Reverse lookup escapes LIKE wildcards (%, _)
  - read_file supports usecols for targeted column reads
  - profile_columns runs in asyncio.to_thread (no longer blocks event loop)
  - Export filters mappings to only the file's columns
  - Review page uses shared api.ts client instead of raw fetch()
- **Deferred:** 7 npm vulnerabilities requiring SvelteKit/Vite major version upgrades (low/moderate severity, dev-server only, local tool)
- **Next review:** 2026-06-22

### 2026-05-16 — v1 shipped
- **Goal:** Build a web-based data anonymization tool with deterministic mappings, format-preserving fakes, and reverse lookup.
- **Outcome:** Shipped. 10 implementation units, 81 backend tests, full UI flow working. Public repo with README and worked example.
- **Deferred:** Portfolio piece on Lailara site, person-vs-product name detection, zip code format-preserving type.
