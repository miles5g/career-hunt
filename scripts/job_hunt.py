#!/usr/bin/env python3
"""
Job hunt — single entry point.

  python scripts/job_hunt.py              # show menu
  python scripts/job_hunt.py onboard      # profile setup (resume first)
  python scripts/job_hunt.py run          # poll ATS + apply pack
  python scripts/job_hunt.py sync         # Simplify CSV merge
  python scripts/job_hunt.py score        # score a pasted JD
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

_SCRIPT_DIR = Path(__file__).resolve().parent
if str(_SCRIPT_DIR) not in sys.path:
    sys.path.insert(0, str(_SCRIPT_DIR))

from profile import load_profile, profile_ready


def cmd_onboard(_: argparse.Namespace) -> None:
    from onboarding import run_onboarding

    run_onboarding()


def cmd_run(args: argparse.Namespace) -> None:
    prof = load_profile()
    if not profile_ready(prof):
        print("\nNo profile yet. Run first:  python scripts/job_hunt.py onboard\n")
    elif args.warn_profile:
        print(f"Using profile (updated {prof.get('updated_at', '?')})\n")

    from find_jobs import run

    run(args.days, args.min_score, args.tier, args.top, school=args.school)


def cmd_sync(args: argparse.Namespace) -> None:
    from sync_simplify import run_sync

    run_sync(file=args.file, dry_run=args.dry_run)


def cmd_score(args: argparse.Namespace) -> None:
    from score_job_listing import main as score_main

    sys.argv = ["score_job_listing.py"]
    if args.file:
        sys.argv.extend(["--file", str(args.file)])
    score_main()


def main() -> None:
    p = argparse.ArgumentParser(
        description="Career job hunt — onboard once, then run.",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python scripts/job_hunt.py onboard
  python scripts/job_hunt.py run
  python scripts/job_hunt.py run --days 45 --top 10
  python scripts/job_hunt.py sync
        """,
    )
    sub = p.add_subparsers(dest="command")

    sub.add_parser("onboard", help="Build profile (resume, interests, comp, personality)")

    run_p = sub.add_parser("run", help="Poll company boards + write apply pack")
    run_p.add_argument("--days", type=int, default=30)
    run_p.add_argument("--min-score", type=int, default=16)
    run_p.add_argument("--tier", choices=["dream_gaming", "dream_tech", "high_odds"], default=None)
    run_p.add_argument("--top", type=int, default=12)
    run_p.add_argument("--school", default=None)
    run_p.add_argument("--warn-profile", action="store_true", default=True)

    sync_p = sub.add_parser("sync", help="Merge latest Simplify export")
    sync_p.add_argument("--file", type=Path, default=None)
    sync_p.add_argument("--dry-run", action="store_true")

    score_p = sub.add_parser("score", help="Score one JD (stdin or --file)")
    score_p.add_argument("--file", type=Path, default=None)

    args = p.parse_args()
    if not args.command:
        print(__doc__ or p.format_help())
        prof = load_profile()
        if profile_ready(prof):
            print(f"\nProfile OK ({prof.get('updated_at')}). Run:  python scripts/job_hunt.py run\n")
        else:
            print("\nStart here:  python scripts/job_hunt.py onboard\n")
        return

    dispatch = {"onboard": cmd_onboard, "run": cmd_run, "sync": cmd_sync, "score": cmd_score}
    dispatch[args.command](args)


if __name__ == "__main__":
    main()
