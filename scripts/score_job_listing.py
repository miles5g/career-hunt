#!/usr/bin/env python3
"""
Score a job description against Miles's application rubric.
Usage:
  python score_job_listing.py < jd.txt
  python score_job_listing.py --file path/to/jd.txt
"""

from __future__ import annotations

import argparse
import json
import re
import sys

# Keywords — tune in APPLICATION_SCORING.md
STRONG_POSITIVE = [
    "product operations", "product ops", "bizops", "business operations",
    "revops", "revenue operations", "implementation specialist", "onboarding",
    "business systems", "process automation", "workflow", "python", "sql",
    "power automate", "zapier", "ai", "saas", "b2b", "cross-functional",
]
WEAK_POSITIVE = ["operations analyst", "systems", "automation", "internal tools"]
NEGATIVE = [
    "help desk", "call center", "customer service", "sdr", "account executive",
    "bookkeeper", "staff accountant", "accounts payable", "accounts receivable",
    "data entry", "trainee", "intern ", "mechanical", "maintenance technician",
]
REMOTE_POSITIVE = ["remote", "work from home", "distributed", "anywhere"]
HYBRID_RISK = ["5 days", "five days", "in office 5", "on-site 5"]
COMP_PATTERN = re.compile(r"\$[\d,]+k?|\b\d{2,3},?\d{3}\s*(?:per year|/yr|annually)", re.I)


def score_text(text: str) -> dict:
    t = text.lower()

    def count_hits(words: list[str]) -> int:
        return sum(1 for w in words if w in t)

    pos = count_hits(STRONG_POSITIVE) + 0.5 * count_hits(WEAK_POSITIVE)
    neg = count_hits(NEGATIVE)

    # Dimension proxies (1-5)
    title_fit = min(5, max(1, int(2 + pos - neg * 0.8)))

    boredom = 5 if any(x in t for x in ["build", "automate", "workflow", "tool", "python", "ai"]) else 3
    if any(x in t for x in ["data entry", "reconcil", "ledger", "journal entry"]) and "automate" not in t:
        boredom = max(1, boredom - 2)

    culture = 4
    if any(x in t for x in REMOTE_POSITIVE):
        culture = 5
    if any(x in t for x in HYBRID_RISK):
        culture = 1
    elif "hybrid" in t and "1 day" not in t and "2 day" not in t:
        culture = 3

    comp = 3
    if COMP_PATTERN.search(text):
        comp = 4
    if re.search(r"\$1[0-4]\d", text) or "100,000" in t or "110,000" in t:
        comp = min(5, comp + 1)
    if "90,000" in t or "$80" in t:
        comp = 2

    win = min(5, max(2, int(3 + pos * 0.3 - neg * 0.5)))
    if "years of experience" in t:
        m = re.search(r"(\d+)\+?\s*years", t)
        if m and int(m.group(1)) >= 6:
            win = max(1, win - 2)

    scores = {
        "fit": title_fit,
        "boredom": boredom,
        "culture": culture,
        "comp": comp,
        "win": win,
    }
    total = sum(scores.values())
    scores["total"] = total
    scores["recommendation"] = "APPLY" if total >= 16 and culture >= 3 and title_fit >= 3 else "SKIP"
    scores["flags"] = []
    if neg >= 3:
        scores["flags"].append("multiple negative keywords")
    if culture <= 2:
        scores["flags"].append("RTO/hybrid concern")
    return scores


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--file", "-f", help="JD text file")
    parser.add_argument("--json", action="store_true", help="JSON output only")
    args = parser.parse_args()

    if args.file:
        text = open(args.file, encoding="utf-8").read()
    else:
        text = sys.stdin.read()

    if not text.strip():
        print("No JD text provided.", file=sys.stderr)
        sys.exit(1)

    result = score_text(text)
    if args.json:
        print(json.dumps(result, indent=2))
        return

    print(f"Recommendation: {result['recommendation']} (total {result['total']}/25)")
    for k in ("fit", "boredom", "culture", "comp", "win"):
        print(f"  {k}: {result[k]}/5")
    if result["flags"]:
        print("Flags:", ", ".join(result["flags"]))


if __name__ == "__main__":
    main()
