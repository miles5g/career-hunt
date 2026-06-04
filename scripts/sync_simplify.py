#!/usr/bin/env python3
"""
Merge new jobs from a Simplify dashboard CSV export into Career tracking.

Simplify has no public API. Best workflow:
  1. https://simplify.jobs/dashboard → Export (Tracked Jobs CSV)
  2. python scripts/sync_simplify.py
  3. Say "fresh list" — applied roles hide via agent_suggested.json + applications.csv

Usage:
  python scripts/sync_simplify.py
  python scripts/sync_simplify.py --file "%USERPROFILE%\\Downloads\\Simplify_Tracked_Jobs_2026-06-04.csv"
  python scripts/sync_simplify.py --since-days 14   # only rows applied in last N days
"""

from __future__ import annotations

import argparse
import csv
import json
import re
import shutil
from datetime import datetime, timedelta
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
DOWNLOADS = Path.home() / "Downloads"
APPLICATIONS_CSV = ROOT / "tracking" / "applications.csv"
AGENT_SUGGESTED = ROOT / "tracking" / "agent_suggested.json"
ARCHIVE_DIR = ROOT / "tracking"

CSV_FIELDS = [
    "date", "company", "title", "source", "url",
    "score_fit", "score_boredom", "score_culture", "score_comp", "score_win",
    "total", "status", "notes", "resume_version", "follow_up_date",
]

SIMPLIFY_GLOB = "Simplify_Tracked_Jobs*.csv"


def norm(s: str) -> str:
    return re.sub(r"\s+", " ", (s or "").strip().lower())


def row_key(row: dict) -> tuple[str, str, str]:
    return (norm(row.get("company", "")), norm(row.get("title", "")), norm(row.get("url", "")))


def find_latest_export(explicit: Path | None) -> Path | None:
    if explicit and explicit.exists():
        return explicit
    candidates = sorted(DOWNLOADS.glob(SIMPLIFY_GLOB), key=lambda p: p.stat().st_mtime, reverse=True)
    return candidates[0] if candidates else None


def direct_url(url: str) -> str:
    u = (url or "").strip()
    if "linkedin.com/jobs/search" in u:
        return u
    return u


def lane(title: str) -> str:
    t = title.lower()
    if any(x in t for x in ("implementation", "onboarding", "technical account", "deployment")):
        return "A-implementation"
    if any(x in t for x in ("automation", "process", "systems", "gtm engineer", "data analyst")):
        return "B-automation"
    if any(x in t for x in ("revops", "revenue ops", "bizops", "business operations", "strategy")):
        return "C-bizops-revops"
    return "other"


def score_job(title: str, company: str, location: str) -> dict[str, int]:
    t, c, loc = title.lower(), company.lower(), (location or "").lower()
    fit = 4 if any(
        x in t for x in (
            "product ops", "bizops", "business operations", "implementation",
            "revops analyst", "strategy and operations", "automation", "process",
        )
    ) else 3
    if any(x in t for x in ("director", "senior manager", "principal")):
        fit = 2
    boredom = 5 if any(x in t for x in ("automation", "systems", "implementation", "product ops")) else 3
    culture = 5 if any(x in loc for x in ("remote", "usa", "united states")) else 4
    if any(x in loc for x in ("mexico", "ireland", "uk", "dallas", "atlanta")):
        culture = 3
    comp, win = 3, 3
    if any(x in c for x in ("openai", "google", "stripe", "discord", "airbnb")):
        win = 2
    if any(x in t for x in ("associate", "analyst", "specialist", "implementation")):
        win = 4
    total = fit + boredom + culture + comp + win
    return {
        "score_fit": fit, "score_boredom": boredom, "score_culture": culture,
        "score_comp": comp, "score_win": win, "total": total,
    }


def parse_simplify_row(r: dict) -> dict | None:
    company = (r.get("Company Name") or r.get("company") or "").strip()
    title = (r.get("Job Title") or r.get("title") or "").strip()
    if not company or not title:
        return None
    status_raw = (r.get("Status") or "").strip().upper()
    status = {"APPLIED": "applied", "SAVED": "saved"}.get(status_raw, status_raw.lower() or "unknown")
    date = (r.get("Applied Date") or r.get("Status Date") or "").strip()
    if date in ("", "N/A"):
        date = datetime.now().strftime("%Y-%m-%d")
    loc = (r.get("Location") or r.get("location") or "").strip()
    jtype = (r.get("job_type") or r.get("Job Type") or "").strip()
    scores = score_job(title, company, loc)
    return {
        "date": date,
        "company": company,
        "title": title,
        "source": "Simplify",
        "url": direct_url(r.get("Job URL") or r.get("url") or ""),
        **scores,
        "status": status,
        "notes": f"lane={lane(title)}; loc={loc}; type={jtype}; simplify_sync",
        "resume_version": "",
        "follow_up_date": "",
    }


def parse_date(s: str) -> datetime | None:
    s = (s or "").strip()
    for fmt in ("%Y-%m-%d", "%m/%d/%Y", "%m/%d/%y"):
        try:
            return datetime.strptime(s[:10], fmt)
        except ValueError:
            continue
    return None


def load_applications() -> tuple[list[dict], dict[tuple[str, str, str], dict]]:
    if not APPLICATIONS_CSV.exists():
        return [], {}
    with APPLICATIONS_CSV.open(newline="", encoding="utf-8") as f:
        rows = list(csv.DictReader(f))
    index = {row_key(r): r for r in rows}
    return rows, index


def load_agent_suggestions() -> list[dict]:
    if not AGENT_SUGGESTED.exists():
        return []
    data = json.loads(AGENT_SUGGESTED.read_text(encoding="utf-8"))
    return list(data.get("suggestions") or [])


def save_agent_suggestions(suggestions: list[dict]) -> None:
    AGENT_SUGGESTED.write_text(
        json.dumps(
            {
                "_comment": "Agent-recommended + Simplify applied roles. Boards stay polled.",
                "suggestions": suggestions,
            },
            indent=2,
        )
        + "\n",
        encoding="utf-8",
    )


def append_agent_suggested(suggestions: list[dict], row: dict) -> bool:
    keys = {
        (norm(s.get("company", "")), norm(s.get("title", "")), norm(s.get("url", "")))
        for s in suggestions
    }
    k = (norm(row["company"]), norm(row["title"]), norm(row.get("url", "")))
    if k in keys:
        return False
    if row.get("status") != "applied":
        return False
    suggestions.append({
        "company": row["company"],
        "title": row["title"],
        "url": row.get("url", ""),
        "suggested_at": datetime.now().strftime("%Y-%m-%d"),
        "note": "Synced from Simplify export",
    })
    return True


def main() -> None:
    p = argparse.ArgumentParser(description="Merge Simplify CSV export into Career tracking.")
    p.add_argument("--file", type=Path, default=None, help="Path to Simplify_Tracked_Jobs CSV")
    p.add_argument("--since-days", type=int, default=0, help="Only import rows applied within N days")
    p.add_argument("--dry-run", action="store_true", help="Print changes without writing")
    args = p.parse_args()

    export = find_latest_export(args.file)
    if not export:
        print("No Simplify export found.")
        print(f"  Export from https://simplify.jobs/dashboard")
        print(f"  Save to Downloads as Simplify_Tracked_Jobs_*.csv")
        print(f"  Or pass --file path")
        raise SystemExit(1)

    print(f"Using: {export}")

    with export.open(newline="", encoding="utf-8-sig") as f:
        simplify_rows = list(csv.DictReader(f))

    cutoff = None
    if args.since_days > 0:
        cutoff = datetime.now() - timedelta(days=args.since_days)

    parsed: list[dict] = []
    for r in simplify_rows:
        row = parse_simplify_row(r)
        if not row:
            continue
        if cutoff:
            dt = parse_date(row["date"])
            if dt and dt < cutoff:
                continue
        parsed.append(row)

    existing, index = load_applications()
    new_rows: list[dict] = []
    updated = 0
    for row in parsed:
        k = row_key(row)
        if k in index:
            prev = index[k]
            if prev.get("status") != row["status"] and row["status"] == "applied":
                prev["status"] = "applied"
                prev["date"] = row["date"] or prev.get("date", "")
                updated += 1
            continue
        new_rows.append(row)
        index[k] = row

    merged = list(index.values())
    merged.sort(key=lambda r: (r.get("date") or "", r.get("company", "")), reverse=True)

    suggestions = load_agent_suggestions()
    added_suggest = 0
    for row in new_rows + [index[k] for k in index if index[k].get("status") == "applied"]:
        if append_agent_suggested(suggestions, row):
            added_suggest += 1

    applied_new = [r for r in new_rows if r["status"] == "applied"]
    saved_new = [r for r in new_rows if r["status"] == "saved"]

    print(f"\nSimplify rows parsed: {len(parsed)}")
    print(f"New to tracker: {len(new_rows)} ({len(applied_new)} applied, {len(saved_new)} saved)")
    print(f"Status updates: {updated}")
    print(f"Added to agent_suggested (fresh-list hide): {added_suggest}")
    print(f"Tracker total: {len(merged)} rows")

    if applied_new:
        print("\nNew APPLIED (hide on next fresh list):")
        for r in applied_new[:15]:
            print(f"  - {r['company']} — {r['title']}")
        if len(applied_new) > 15:
            print(f"  ... +{len(applied_new) - 15} more")

    if args.dry_run:
        print("\n(dry-run: no files written)")
        return

    APPLICATIONS_CSV.parent.mkdir(parents=True, exist_ok=True)
    with APPLICATIONS_CSV.open("w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=CSV_FIELDS, extrasaction="ignore")
        w.writeheader()
        w.writerows(merged)

    archive = ARCHIVE_DIR / f"simplify_export_{datetime.now().strftime('%Y-%m-%d')}.csv"
    shutil.copy2(export, archive)
    save_agent_suggestions(suggestions)
    print(f"\nWrote: {APPLICATIONS_CSV}")
    print(f"Archive: {archive}")
    print(f"Updated: {AGENT_SUGGESTED}")


if __name__ == "__main__":
    main()
