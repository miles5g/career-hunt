# Simplify history import

## Can we scrape Simplify automatically?

**Partially yes.** Your Chrome extension stores data locally (LevelDB). We extracted **company names** (~77 unique) from:

`Chrome Profile 4` → Simplify Copilot extension (`pbanhockgagggenencehbnadejlgchfc`)

**Not in the local blob (reliably):** job titles, applied dates, status — those live on Simplify's cloud dashboard.

## Full export (done 2026-05-20)

Imported from `Downloads/Simplify_Tracked_Jobs_2026-05-20.csv`:

- **84 jobs** → `tracking/applications.csv`
- Analysis → `tracking/SIMPLIFY_ANALYSIS.md`

```powershell
.\scripts\import_simplify_csv.ps1 -InputCsv "$env:USERPROFILE\Downloads\Simplify_Tracked_Jobs_2026-05-20.csv"
```

## Best path (merge, does not wipe your tracker)

1. [Simplify dashboard](https://simplify.jobs/dashboard) → **Export** tracked jobs CSV  
2. File lands in `Downloads` as `Simplify_Tracked_Jobs_*.csv`  
3. Run:

```powershell
python scripts/sync_simplify.py
```

This **merges** new rows into `tracking/applications.csv` and adds **applied** jobs to `tracking/agent_suggested.json` so the ATS **fresh list** stops repeating them.

Options:

```powershell
python scripts/sync_simplify.py --since-days 14
python scripts/sync_simplify.py --file "C:\path\to\export.csv"
python scripts/sync_simplify.py --dry-run
```

## Legacy full replace (avoid)

`import_simplify_csv.ps1` **overwrites** `applications.csv`. Use `sync_simplify.py` instead unless you want a full replace from one export.

## Automated import (companies only)

```powershell
cd "c:\Users\owner\Documents\Cursor Projects\Career"
.\scripts\import_simplify_history.ps1
```

Output: `tracking/simplify_import.csv`

Re-run after closing Chrome for a fresher snapshot.

## Sample companies found in your extension data

Includes (partial): Hopper, Owner.com, Lean Layer, Discord, Riot Games, Waymo, Airbnb, OpenAI, Google, Dandy, Headway, SeatGeek, Whatnot, Tiger Analytics, Insight Global, and others.

Use this to see **volume** and **lane** (many are ops/tech; some are staffing agencies — Insight Global, etc.).

## Merge into main tracker

Manually or ask Cursor: map `simplify_import.csv` → `applications.csv` with `source=Simplify`.
