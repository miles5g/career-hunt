#!/usr/bin/env python3
"""Log a role the agent recommended (e.g. from a pasted Wellfound card)."""
from __future__ import annotations

import argparse
import json
from datetime import datetime
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
AGENT_SUGGESTED = ROOT / "tracking" / "agent_suggested.json"


def main() -> None:
    p = argparse.ArgumentParser(description="Record an agent-suggested role for fresh-list filtering.")
    p.add_argument("--company", required=True)
    p.add_argument("--title", required=True)
    p.add_argument("--url", default="")
    p.add_argument("--note", default="")
    args = p.parse_args()

    data = {"_comment": "", "suggestions": []}
    if AGENT_SUGGESTED.exists():
        data = json.loads(AGENT_SUGGESTED.read_text(encoding="utf-8"))

    data["suggestions"].append({
        "company": args.company,
        "title": args.title,
        "url": args.url,
        "suggested_at": datetime.now().strftime("%Y-%m-%d"),
        **({"note": args.note} if args.note else {}),
    })
    data["_comment"] = "Agent-recommended roles only. Boards stay polled for new postings."
    AGENT_SUGGESTED.write_text(json.dumps(data, indent=2) + "\n", encoding="utf-8")
    print(f"Logged: {args.company} — {args.title}")


if __name__ == "__main__":
    main()
