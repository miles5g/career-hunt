#!/usr/bin/env python3
"""Generate LinkedIn outreach: alumni (primary) and recruiter (backup)."""

from __future__ import annotations

import json
import re
from pathlib import Path

CONFIG_PATH = Path(__file__).resolve().parent / "outreach_config.json"

# LinkedIn connection request note limit (characters; keep ASCII for Windows consoles)
CONNECTION_NOTE_MAX = 300


def load_config() -> dict:
    return json.loads(CONFIG_PATH.read_text(encoding="utf-8"))


def slugify(text: str) -> str:
    s = re.sub(r"[^a-z0-9]+", "-", (text or "").lower()).strip("-")
    return s[:80] or "company"


def pick_school(school_arg: str | None, config: dict) -> dict:
    schools = config.get("schools") or []
    if not schools:
        return {"name": "your school", "short": "school", "linkedin_company_filter": ""}
    if school_arg:
        key = school_arg.strip().lower()
        for s in schools:
            if key in (s.get("short", "").lower(), s.get("name", "").lower()):
                return s
    primary = (config.get("primary_school") or "").strip().lower()
    if primary:
        for s in schools:
            if primary in (s.get("short", "").lower(), s.get("name", "").lower()):
                return s
    return schools[0]


def alumni_batch_connection_note(
    *,
    company: str,
    title: str,
    school: dict,
    config: dict,
) -> str:
    """One LinkedIn connection note for many alumni. Replace [First name]. Not InMail."""
    short = school.get("short") or school.get("name", "school")
    co = company.strip()
    role = title.strip()
    lines = [
        "Hi [First name], fellow " + short + " alum.",
        f"Exploring {role} at {co} and would value a quick inside view.",
        "Ops/automation background (Python/VBA/LLMs). No formal referral needed. Thanks.",
    ]
    note = " ".join(lines)
    if len(note) > CONNECTION_NOTE_MAX:
        note = (
            f"Hi [First name], {short} alum. Exploring {role} at {co}. "
            "Ops/automation background. Quick perspective appreciated. Thanks."
        )
    return note[:CONNECTION_NOTE_MAX]


def alumni_connection_note(
    *,
    first_name: str,
    company: str,
    title: str,
    school: dict,
    config: dict,
) -> str:
    """Short note for LinkedIn connection request (<=300 chars when possible)."""
    name = first_name.strip() or "there"
    short = school.get("short") or school.get("name", "school")
    co = company.strip()
    role = title.strip()
    lines = [
        f"Hi {name}, fellow {short} alum here.",
        f"I'm looking at {role} at {co} and would value a 10-min perspective from someone on the inside.",
        "I work in ops automation (Python/VBA/LLMs). Thanks either way.",
    ]
    note = " ".join(lines)
    if len(note) > CONNECTION_NOTE_MAX:
        note = (
            f"Hi {name}, {short} alum. Exploring {role} at {co}. "
            f"Ops/automation background. Open to a brief chat? Thanks."
        )
    return note[:CONNECTION_NOTE_MAX]


def alumni_message(
    *,
    first_name: str,
    company: str,
    title: str,
    role_url: str,
    school: dict,
    config: dict,
) -> str:
    """Full message after connect or InMail."""
    name = first_name.strip() or "there"
    short = school.get("short") or school.get("name", "school")
    proof = config.get("proof_line", "").strip()
    ask = config.get("alumni_ask", "").strip()
    sender = config.get("sender_name", "Miles Johnson")
    parts = [
        f"Hi {name},",
        "",
        f"I'm {sender}, also {school.get('name', short)}. I saw you're at {company} and I'm looking closely at the "
        f"{title} opening" + (f" ({role_url})" if role_url else "") + ".",
        "",
        proof,
        "",
        "My lane is " + (config.get("target_blurb") or "ops and systems work") + ". "
        "I'm not asking you to refer me blindly. I'd like to understand the team and whether this role is "
        "mostly build/systems vs ticket-chasing.",
        "",
        ask,
        "",
        "Thanks for reading.",
        sender,
    ]
    return "\n".join(parts)


def recruiter_message(
    *,
    company: str,
    title: str,
    role_url: str,
    config: dict,
) -> str:
    """Backup when no alumni reply or no alumni at company."""
    sender = config.get("sender_name", "Miles Johnson")
    proof = config.get("proof_line", "").strip()
    ask = config.get("recruiter_ask", "").strip()
    parts = [
        f"Hi,",
        "",
        f"I'm {sender}. I applied for (or am about to apply for) {title} at {company}."
        + (f" Link: {role_url}" if role_url else ""),
        "",
        proof,
        "",
        ask,
        "",
        "Happy to send a one-page summary of relevant builds (GitHub: "
        + (config.get("github") or "on request") + ").",
        "",
        "Thanks,",
        sender,
    ]
    return "\n".join(parts)


def linkedin_alumni_search_url(company: str, school: dict) -> str:
    """LinkedIn people search: company + school filter (open in browser, adjust filters)."""
    from urllib.parse import quote

    q = f"{company} {school.get('linkedin_company_filter') or school.get('name', '')}"
    return "https://www.linkedin.com/search/results/people/?keywords=" + quote(q)


def format_outreach_markdown(
    *,
    company: str,
    title: str,
    role_url: str,
    first_name: str,
    school_arg: str | None,
    config: dict | None = None,
) -> str:
    config = config or load_config()
    school = pick_school(school_arg, config)
    search_url = linkedin_alumni_search_url(company, school)

    conn = alumni_connection_note(
        first_name=first_name,
        company=company,
        title=title,
        school=school,
        config=config,
    )
    alum = alumni_message(
        first_name=first_name,
        company=company,
        title=title,
        role_url=role_url,
        school=school,
        config=config,
    )
    rec = recruiter_message(company=company, title=title, role_url=role_url, config=config)

    lines = [
        f"# LinkedIn outreach — {company}",
        "",
        f"**Role:** {title}  ",
        f"**Apply link:** {role_url or '(add URL)'}  ",
        f"**School filter:** {school.get('name')} (`{school.get('short')}`)",
        "",
        "## 1. Find alumni (do this first)",
        "",
        f"1. Open [LinkedIn people search]({search_url}).",
        "2. Filter: **Current company** = `" + company + "`.",
        "3. Filter: **School** = `" + (school.get("linkedin_company_filter") or school.get("name", "")) + "`.",
        "4. Pick ops/revops/product ops/strategy titles (avoid recruiters for the alumni note).",
        "5. If the listing shows **N school alumni work here**, start with 2nd-degree ops people.",
        "",
        "**If no alumni:** use section 3 (recruiter) below. Try the other school in `outreach_config.json` before giving up.",
        "",
        "## 2. Message to alumni",
        "",
        "### Connection request (max 300 chars)",
        "",
        "```",
        conn,
        "```",
        "",
        f"_{len(conn)} characters_",
        "",
        "### After they accept (or InMail)",
        "",
        "```",
        alum,
        "```",
        "",
        "## 3. Backup: recruiter / talent",
        "",
        "Use if no alumni responds in ~5 business days or none listed.",
        "",
        "```",
        rec,
        "```",
        "",
        "## Checklist",
        "",
        "- [ ] Alumni search done",
        "- [ ] Connection or InMail sent",
        "- [ ] Application submitted after message (same day)",
        "- [ ] Logged in `tracking/applications.csv`",
        "",
    ]
    return "\n".join(lines)


def apply_pack_outreach_block(
    *,
    company: str,
    title: str,
    role_url: str,
    config: dict | None = None,
    school_arg: str | None = None,
) -> list[str]:
    """One alumni connection note for job_hunt_apply_pack.md (batch paste, not InMail)."""
    config = config or load_config()
    school = pick_school(school_arg, config)
    search_url = linkedin_alumni_search_url(company, school)
    note = alumni_batch_connection_note(
        company=company,
        title=title,
        school=school,
        config=config,
    )
    other = ""
    schools = config.get("schools") or []
    if len(schools) > 1:
        alt = [s for s in schools if s is not school]
        if alt:
            other = f" Other school: `{alt[0].get('short')}` via `--school` or `primary_school` in config."
    return [
        f"**Alumni note ({school.get('short', school.get('name'))})** — "
        f"[search]({search_url}) · replace `[First name]` · not InMail",
        "",
        note,
        "",
        f"({len(note)}/300 chars){other}",
        "",
    ]
