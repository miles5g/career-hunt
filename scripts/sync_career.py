#!/usr/bin/env python3
"""
Pull GitHub career-hunt into this folder (laptop) or report sync status (phone/cloud).

GitHub is the shared folder. Phone cloud VMs cannot see OneDrive/iCloud/laptop disks.

  python scripts/job_hunt.py pull
  python scripts/job_hunt.py pull --status
"""

from __future__ import annotations

import argparse
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
PIPELINE = ROOT / "tracking" / "LIVE_PIPELINE.md"
GITIGNORED = [
    "context/USER_CONTEXT.md",
    "context/job_hunt_profile.json",
    "tracking/applications.csv",
]


def _git(args: list[str]) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        ["git", *args],
        cwd=ROOT,
        text=True,
        capture_output=True,
    )


def _git_ok(args: list[str]) -> str:
    r = _git(args)
    if r.returncode != 0:
        err = (r.stderr or r.stdout or "").strip()
        raise SystemExit(f"git {' '.join(args)} failed: {err}")
    return (r.stdout or "").strip()


def cmd_status() -> None:
    branch = _git_ok(["rev-parse", "--abbrev-ref", "HEAD"])
    _git(["fetch", "origin", "main"])
    behind = _git_ok(["rev-list", "--count", "HEAD..origin/main"])
    ahead = _git_ok(["rev-list", "--count", "origin/main..HEAD"])
    dirty = _git_ok(["status", "--porcelain"])
    pipe_age = "missing"
    if PIPELINE.exists():
        first = PIPELINE.read_text(encoding="utf-8").splitlines()[:4]
        pipe_age = next((ln for ln in first if "synced" in ln.lower() or "Last" in ln), first[0])

    print(f"Folder:  {ROOT}")
    print(f"Branch:  {branch}")
    print(f"vs main: {behind} commit(s) behind origin/main, {ahead} ahead")
    print(f"Dirty:   {'yes' if dirty else 'no'}")
    print(f"Pipeline:{pipe_age}")
    print()
    print("Gitignored (laptop-only, never on phone agents):")
    for rel in GITIGNORED:
        p = ROOT / rel
        print(f"  {'present' if p.exists() else 'absent ':7} {rel}")


def cmd_pull() -> None:
    cmd_status()
    branch = _git_ok(["rev-parse", "--abbrev-ref", "HEAD"])
    dirty = _git_ok(["status", "--porcelain"])
    if dirty:
        print("\nUncommitted local files. Not pulling. Commit or stash first.")
        return
    if branch != "main":
        print(f"\nOn {branch}, not main. Fetch done. Merge or rebase onto origin/main if you want those files.")
        return
    r = _git(["pull", "origin", "main"])
    sys.stdout.write(r.stdout or "")
    if r.returncode != 0:
        sys.stderr.write(r.stderr or "")
        raise SystemExit(r.returncode)
    print("Laptop folder matches origin/main for committed files.")


def main() -> None:
    p = argparse.ArgumentParser(description="Sync this Career folder with GitHub.")
    p.add_argument("--status", action="store_true", help="Fetch and report, do not pull")
    args = p.parse_args()
    if args.status:
        cmd_status()
    else:
        cmd_pull()


if __name__ == "__main__":
    main()
