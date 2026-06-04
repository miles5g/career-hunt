#!/usr/bin/env python3
"""
Generate LinkedIn outreach for a target role: alumni message + recruiter backup.

Usage:
  python scripts/gen_linkedin_outreach.py --company Rain --title "Senior Revenue Operations Analyst"
  python scripts/gen_linkedin_outreach.py --company Paragon --title "Operations Associate" \\
      --url "https://jobs.ashbyhq.com/..." --alumni-first Alex --school UCSB
  python scripts/gen_linkedin_outreach.py --from-pack 3
"""

from __future__ import annotations

import argparse
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(Path(__file__).resolve().parent))

from linkedin_outreach import format_outreach_markdown, load_config, slugify

OUT_DIR = ROOT / "tracking" / "outreach"
APPLY_PACK = ROOT / "tracking" / "job_hunt_apply_pack.md"


def parse_apply_pack(index: int) -> tuple[str, str, str]:
    if not APPLY_PACK.exists():
        raise SystemExit(f"Apply pack not found: {APPLY_PACK}")
    text = APPLY_PACK.read_text(encoding="utf-8")
    blocks = re.split(r"\n---\n", text)
    roles = []
    for block in blocks:
        m_co = re.search(r"^## \d+\. (.+?) — (.+)$", block, re.M)
        m_url = re.search(r"\*\*Apply:\*\* (\S+)", block)
        if m_co:
            roles.append((m_co.group(1).strip(), m_co.group(2).strip(), (m_url.group(1) if m_url else "")))
    if index < 1 or index > len(roles):
        raise SystemExit(f"Pack index {index} out of range (1-{len(roles)} roles in apply pack).")
    return roles[index - 1]


def main() -> None:
    p = argparse.ArgumentParser(description="Generate LinkedIn alumni + recruiter outreach.")
    p.add_argument("--company", help="Company name")
    p.add_argument("--title", help="Job title")
    p.add_argument("--url", default="", help="Application URL")
    p.add_argument("--alumni-first", default="", help="Alumni first name for personalization")
    p.add_argument("--school", default=None, help="UCSB or Penn State (default: first in config)")
    p.add_argument("--from-pack", type=int, metavar="N", help="Use role #N from job_hunt_apply_pack.md")
    p.add_argument("--stdout", action="store_true", help="Print only, do not write file")
    p.add_argument("-o", "--output", help="Output markdown path")
    args = p.parse_args()

    if args.from_pack:
        company, title, url = parse_apply_pack(args.from_pack)
    else:
        if not args.company or not args.title:
            p.error("Provide --company and --title, or --from-pack N")
        company, title, url = args.company, args.title, args.url or ""

    md = format_outreach_markdown(
        company=company,
        title=title,
        role_url=url,
        first_name=args.alumni_first,
        school_arg=args.school,
        config=load_config(),
    )

    if args.stdout:
        print(md)
        return

    out = Path(args.output) if args.output else OUT_DIR / f"{slugify(company)}-{slugify(title)[:40]}.md"
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(md, encoding="utf-8")
    print(f"Wrote: {out}")


if __name__ == "__main__":
    main()
