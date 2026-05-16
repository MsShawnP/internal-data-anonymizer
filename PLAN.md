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

- [ ] End-to-end browser testing of full flow
- [ ] README with worked example
- [ ] Portfolio piece on Lailara site

## Definition of done for this arc

- [ ] Tool accepts CSV/XLSX/JSON/Parquet and outputs in user-chosen format
- [ ] Web UI shows proposed mappings and allows editing before apply
- [ ] Deterministic: same input + same project = same output across runs/files
- [ ] Numeric columns preserve distribution shape visually and statistically
- [ ] Format-preserving fakes for structured identifiers (UPC, GTIN, phone, ZIP)
- [ ] Dirty-data fidelity: invalid originals produce invalid fakes at same rate
- [ ] Reverse lookup available in UI for the operator
- [ ] Project-level mapping persistence
- [ ] Public GitHub repo with README and worked example
- [ ] One portfolio piece on Lailara site using the tool's output

---

## Arc history

When an arc completes, archive its goal, completion date, and outcome
here. Then start a new arc above. Provides continuity without bloating
the active plan.
