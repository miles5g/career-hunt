# Application automation roadmap

**Principle:** Automate **discovery, scoring, and paperwork prep** — not blind submitting.

---

## What to automate (recommended)

| Step | Automate? | Tool | Notes |
|------|-----------|------|-------|
| Pull new jobs from saved searches | Partial | LinkedIn has no official API for jobs; manual export or browser extension | Phase 2 |
| Parse JD text | Yes | Python + paste or scrape | Extract title, salary, remote, keywords |
| Score vs rubric | Yes | `scripts/score_job_listing.py` + LLM | Human confirms |
| Tailor resume bullets | Yes | Cursor / template swap | 3 PDF variants, pick per lane |
| Generate cover blurb | Yes | Cursor with USER_CONTEXT | 150 words max |
| Track in CSV | Yes | applications.csv | Source of truth |
| Click Easy Apply | **No** (default) | — | Quality + LinkedIn ToS risk |
| Answer custom questions | Semi | Bank of STAR stories | Review each |

---

## Phase 2 — scripts (build in Career repo)

### `scripts/score_job_listing.py`

- Input: JD text (stdin or file)
- Output: JSON scores + apply/skip + missing keywords
- Uses rubric from `APPLICATION_SCORING.md`

### `scripts/append_application.py`

- CLI: company, title, url, scores → append CSV row

### `scripts/tailor_bullet.py` (later)

- Input: JD + role lane (product_ops | automation | implementation)
- Output: 3 suggested resume bullets

---

## Phase 3 — browser assist (optional)

- **Playwright** logged-in session: fragile, breaks on UI changes, account risk
- Safer: **Magical / Simplify** style extensions for autofill only
- **Not recommended:** mass Easy Apply bots

---

## Gemini vs Cursor division

| Task | Use |
|------|-----|
| Batch “which of 40 jobs?” | **Stop** — use scoring script + 5 min human pass |
| One JD deep dive | Cursor with `context/USER_CONTEXT.md` |
| Cover letter | Cursor |
| Career strategy | This repo + Cursor |

---

## Data model (`applications.csv`)

Keep one row per application. Status values:

`planned` → `applied` → `heard_nothing` | `rejected` | `phone_screen` | `onsite` | `offer` | `withdrawn`

Review weekly: conversion by `source` and `lane` (A/B/C).

---

## Legal / ethics

- LinkedIn Prohibited: scrapers, bots that misrepresent you
- Always review AI-generated answers before submit
- Never lie about skills — frame projects as “built in production/prototype”
