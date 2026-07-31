# internal-data-anonymizer — Failure Log

What was attempted that didn't work, why it didn't work, and what was
tried next.

Lower bar than DECISIONS.md — capture failures even when they didn't
produce a durable rule. The whole point: future-you (or future-Claude)
shouldn't re-attempt dead ends because the lesson got lost.

---

## Format

### YYYY-MM-DD — [One-line failure description]

**Attempted:** [What was tried]

**Why it didn't work:** [Concrete reason, not "it broke." If the
failure mode was technical, name the specific issue. If the failure
mode was scope or approach, name that.]

**What we tried instead:** [The next attempt, which may also have
failed and may have its own entry below]

**Status:** Resolved / open / abandoned

**Tags:** [keywords for future text-search]

---

## Entries

[New entries get added here, most recent at the top]

### 2026-07-31 — JSON reader parity via read_json(dtype=str) + fillna

**Attempted:** Fix the JSON reader to match CSV/XLSX (string-typed, blanks as "") by `pd.read_json(path, dtype=str)` then `.fillna("")`.

**Why it didn't work:** `read_json(dtype=str)` stringifies JSON `null` into the literal string `"None"` — so `fillna` never sees a NaN to fill, and the blank stays `"None"`. Worse, it's indistinguishable from a genuine `"None"` string value, so any post-hoc `replace("None","")` would wrongly blank real data (bad for a tool that handles dirty data). A second attempt (`read_json` without dtype, then `fillna("").astype(str)`) also failed: read_json infers `"1"` as numeric `1.0`, corrupting the representation.

**What we tried instead:** Parse the file with the stdlib `json` module, build the DataFrame from records (preserves each value's representation and keeps true nulls as None/NaN), then map `None/NaN → ""` and everything else → `str`. This is now `_read_json` in ingest.py.

**Status:** Resolved

**Tags:** pandas, read_json, dtype, null-handling, ingest, json
