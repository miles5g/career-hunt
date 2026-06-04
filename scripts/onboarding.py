#!/usr/bin/env python3
"""
Interactive job hunt profile setup — one question at a time, no forms/tabs.

Writes context/job_hunt_profile.json and context/USER_CONTEXT.md (local, gitignored).
"""

from __future__ import annotations

import json
import re
import sys
from pathlib import Path

from profile import (
    USER_CONTEXT_PATH,
    default_profile,
    extract_resume_signals,
    save_profile,
    write_user_context_md,
)

ROOT = Path(__file__).resolve().parent.parent


def _say(msg: str) -> None:
    print(msg)


def _ask(prompt: str, default: str = "") -> str:
    suffix = f" [{default}]" if default else ""
    val = input(f"\n{prompt}{suffix}\n> ").strip()
    return val or default


def _ask_multiline(header: str) -> list[str]:
    _say(header)
    _say("(Enter one item per line. Blank line when done.)")
    lines: list[str] = []
    while True:
        line = input("> ").strip()
        if not line:
            break
        lines.append(line)
    return lines


def _read_resume(path: Path) -> str:
    if path.suffix.lower() == ".pdf":
        try:
            from pypdf import PdfReader  # type: ignore
        except ImportError:
            _say("Install pypdf for PDF: pip install pypdf")
            _say("Or save resume as .md / .txt and run again.")
            return ""
        reader = PdfReader(str(path))
        return "\n".join(page.extract_text() or "" for page in reader.pages)
    return path.read_text(encoding="utf-8", errors="replace")


def _likert(question: str, labels: tuple[str, ...]) -> str:
    _say(question)
    for i, lab in enumerate(labels, 1):
        _say(f"  {i}. {lab}")
    while True:
        raw = input("> ").strip()
        if raw.isdigit() and 1 <= int(raw) <= len(labels):
            return labels[int(raw) - 1]
        if raw in labels:
            return raw
        _say(f"Pick 1-{len(labels)} or type the option.")


def _sync_outreach_school(profile: dict) -> None:
    school = (profile.get("personality") or {}).get("primary_school", "")
    if not school:
        return
    cfg_path = Path(__file__).resolve().parent / "outreach_config.json"
    if not cfg_path.exists():
        return
    try:
        cfg = json.loads(cfg_path.read_text(encoding="utf-8"))
        cfg["primary_school"] = school
        cfg_path.write_text(json.dumps(cfg, indent=2) + "\n", encoding="utf-8")
    except (json.JSONDecodeError, OSError):
        pass


def adaptive_followups(profile: dict) -> list[str]:
    """Extra questions based on what they already said."""
    notes: list[str] = []
    interests = " ".join(profile.get("interests") or []).lower()
    dis = " ".join(profile.get("disinterests") or []).lower()
    questions: list[tuple[str, str]] = []

    if "game" in interests or "gaming" in interests:
        questions.append(
            (
                "Gaming showed up in interests. Is games your primary lane or secondary (10% effort)?",
                "gaming_lane",
            )
        )
    if "accounting" in dis or "finance" in dis:
        questions.append(
            (
                "You want to avoid accounting grind. Is finance-adjacent ops OK (RevOps, BizOps at fintech)?",
                "finance_adjacent_ok",
            )
        )
    if "manager" in dis or "director" in dis:
        questions.append(
            (
                "Senior IC titles (Senior Analyst) OK, or only Associate/Analyst level?",
                "senior_ic_ok",
            )
        )
    if profile.get("compensation", {}).get("floor_usd", 0) >= 140_000:
        questions.append(
            (
                "High comp floor: OK with fewer applications and longer search?",
                "patient_search",
            )
        )
    if "remote" in interests or profile.get("location", {}).get("remote_us"):
        questions.append(
            (
                "Any hybrid city you would actually commute to weekly? (city name or 'none')",
                "hybrid_commute",
            )
        )

    for q, key in questions[:4]:
        ans = _ask(q)
        profile.setdefault("personality", {})[key] = ans
        notes.append(f"{key}: {ans}")

    return notes


def run_onboarding() -> dict:
    _say("=" * 60)
    _say("  JOB HUNT SETUP")
    _say("  One question at a time. Takes ~8-12 minutes.")
    _say("  Builds your profile so the poller ranks jobs YOU would like.")
    _say("=" * 60)

    profile = default_profile()

    # --- Resume first ---
    _say("\n--- Step 1: Resume ---")
    resume_path = _ask(
        "Path to resume file (.md, .txt, or .pdf)",
        "",
    )
    resume_text = ""
    rp = Path(resume_path).expanduser()
    if rp.is_file():
        resume_text = _read_resume(rp)
        profile["resume"]["path"] = str(rp)
        signals = extract_resume_signals(resume_text)
        profile["resume"]["signals"] = signals
        profile["resume"]["text_preview"] = resume_text[:2000]
        _say(f"\nExtracted from resume: skills={signals.get('skills')}, titles={signals.get('title_signals')}")
    else:
        _say("File not found. Paste resume text (blank line, then END on its own line).")
        buf: list[str] = []
        while True:
            line = input()
            if line.strip() == "END":
                break
            buf.append(line)
        resume_text = "\n".join(buf)
        profile["resume"]["text_preview"] = resume_text[:2000]
        profile["resume"]["signals"] = extract_resume_signals(resume_text)

    # --- Identity (not always on resume) ---
    _say("\n--- Step 2: Contact (if not obvious from resume) ---")
    profile["identity"]["name"] = _ask("Full name")
    profile["identity"]["email"] = _ask("Email")
    profile["identity"]["linkedin"] = _ask("LinkedIn URL")
    profile["identity"]["github"] = _ask("GitHub URL")

    # --- Location ---
    _say("\n--- Step 3: Location ---")
    remote = _ask("Require fully remote US? (yes/no)", "yes").lower().startswith("y")
    profile["location"]["remote_us"] = remote
    hybrid = _ask(
        "Hybrid cities you'd commute to (comma-separated, e.g. Santa Monica, Los Angeles)",
        "Santa Monica",
    )
    profile["location"]["hybrid_cities"] = [c.strip() for c in hybrid.split(",") if c.strip()]
    profile["location"]["max_office_days_per_week"] = int(
        _ask("Max in-office days per week for hybrid", "2") or "2"
    )
    exclude = _ask(
        "Cities/regions to auto-skip (comma-separated)",
        "New York, San Francisco, Seattle, Chicago, Boston",
    )
    profile["location"]["exclude_cities"] = [c.strip().lower() for c in exclude.split(",") if c.strip()]
    profile["location"]["notes"] = _ask("Where you live (city, state)", "Santa Monica, CA")

    # --- Compensation ---
    _say("\n--- Step 4: Compensation ---")
    floor = _ask("Minimum base salary (USD, no commas)", "100000")
    profile["compensation"]["floor_usd"] = int(re.sub(r"[^\d]", "", floor) or "100000")
    tlo = _ask("Target range low (USD)", "120000")
    thi = _ask("Target range high (USD)", "150000")
    profile["compensation"]["target_low_usd"] = int(re.sub(r"[^\d]", "", tlo) or "120000")
    profile["compensation"]["target_high_usd"] = int(re.sub(r"[^\d]", "", thi) or "150000")

    # --- Interests / disinterests (detailed) ---
    _say("\n--- Step 5: What you WANT (be specific) ---")
    profile["interests"] = _ask_multiline(
        "Interests: role types, industries, work activities (automation, AI, RevOps, etc.)"
    )
    _say("\n--- Step 6: What you REFUSE ---")
    profile["disinterests"] = _ask_multiline(
        "Disinterests: titles, cultures, tasks (accounting grind, 5x RTO, SDR, etc.)"
    )

    profile["role_preferences"]["titles_love"] = _ask_multiline(
        "Title keywords you are excited to see (one per line, optional — Enter to skip)"
    ) or profile["interests"][:5]
    profile["role_preferences"]["titles_avoid"] = _ask_multiline(
        "Title keywords that mean instant skip (optional — Enter to skip)"
    ) or profile["disinterests"][:5]

    # --- Personality (short "test") ---
    _say("\n--- Step 7: How you work (pick closest option) ---")
    profile["personality"]["builder_vs_operator"] = _likert(
        "Manual repetitive work feels like:",
        ("A bug to automate away", "Fine if paid well", "Most of the job is OK"),
    )
    profile["personality"]["ambiguity"] = _likert(
        "Undefined problems with no playbook:",
        ("Energy — I like shaping the system", "OK with guidance", "Prefer clear SOPs"),
    )
    profile["personality"]["stakeholders"] = _likert(
        "Cross-functional meetings and alignment:",
        ("Necessary, keep short", "Neutral", "Favorite part of the job"),
    )
    profile["personality"]["depth"] = _likert(
        "Ideal depth:",
        ("Hands-on tools + code", "Mix strategy and execution", "Mostly strategy/docs"),
    )
    profile["personality"]["pace"] = _likert(
        "Best environment:",
        ("Startup / move fast", "Mid-size", "Large corp with process"),
    )
    profile["personality"]["boredom_trigger"] = _ask(
        "What makes you quit mentally fastest? (one sentence)",
        "Manual data entry with no mandate to fix the system",
    )

    # --- Adaptive follow-ups ---
    _say("\n--- Step 8: Follow-up questions (based on your answers) ---")
    profile["followup_notes"] = adaptive_followups(profile)

    # --- Outreach defaults ---
    _say("\n--- Step 9: Alumni outreach (optional) ---")
    school = _ask("Primary school for LinkedIn alumni notes (short name)", "UCSB")
    profile["personality"]["primary_school"] = school

    profile["onboarding_complete"] = True
    path = save_profile(profile)
    ctx = write_user_context_md(profile)
    _sync_outreach_school(profile)

    _say("\n" + "=" * 60)
    _say("  DONE")
    _say(f"  Profile: {path}")
    _say(f"  Agent context: {ctx}")
    _say("\n  Next: python scripts/job_hunt.py run")
    _say("  In Cursor: say 'run the job hunt' or 'fresh list'")
    _say("=" * 60)
    return profile


def main() -> None:
    try:
        run_onboarding()
    except KeyboardInterrupt:
        _say("\nCancelled. Partial profile not saved.")
        sys.exit(1)


if __name__ == "__main__":
    main()
