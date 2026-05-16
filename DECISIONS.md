# internal-data-anonymizer — Decisions Log

Permanent record of choices that should survive session turnover.
If a decision is reversed, strike it through and add the replacement
below — don't delete.

---

## Format

Each entry:
- **Date** — when decided
- **Decision** — one sentence, imperative voice
- **Why** — the reasoning, including what was tried and rejected
- **Scope** — what this applies to (file, chunk, deliverable, or "global")
- **Do not** — explicit anti-instructions, if any

---

## Architecture & Pipeline

### 2026-05-16 — Two-tier SQLite design
- **Decision:** Use root `app.db` for project metadata (single lifespan connection) + per-project `mappings.db` files (connection-per-request via `get_project_db()`).
- **Why:** Per-project isolation makes deletion trivial (rm the dir), avoids cross-project query accidents, keeps individual DBs small. Root DB holds only the project list.
- **Scope:** Global (backend/app/db.py)
- **Do not:** Share a single DB for all projects' mappings.

### 2026-05-16 — Deterministic seeding via SHA-256
- **Decision:** Use `int(hashlib.sha256((project_salt + column_name + original_value).encode()).hexdigest(), 16)` as Faker seed. Stored mappings are authoritative after approval.
- **Why:** Python's built-in `hash()` is non-deterministic across runs (PYTHONHASHSEED). SHA-256 is stable, reproducible, and sufficiently random for seeding.
- **Scope:** backend/app/services/engine.py
- **Do not:** Use Python's `hash()` for deterministic seeding.

### 2026-05-16 — FastAPI + SvelteKit SPA monorepo
- **Decision:** Backend FastAPI (port 8000), frontend SvelteKit in SPA/static mode (port 5173 dev, adapter-static for build). Vite proxies `/api` to backend.
- **Why:** Lightweight, fast local dev, no SSR needed for a local tool. Svelte 5 runes for reactive state.
- **Scope:** Global
- **Do not:** Add SSR or server-side rendering — this is a local tool.

---

## Data & Schema

[Decisions about data sources, schemas, transformations]

---

## Output Formats

[Decisions about deliverable formats, structure, organization]

---

## Reversed / Superseded

When a decision is overturned:
1. Strike through the original entry above (don't delete)
2. Add a new entry below with the replacement decision
3. Note the link in both directions

This preserves the history of why something is the way it is.
