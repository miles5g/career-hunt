#!/usr/bin/env python3
"""JD-specific cover letters and one alumni connection note for the apply pack."""

from __future__ import annotations

import html
import re

from linkedin_outreach import alumni_batch_connection_note, load_config

JD_HOOKS = [
    ("automation", "The posting calls out automation, which is where I have shipped the most."),
    ("workflow", "You mention workflows; I build and maintain those in production today."),
    ("python", "Python is in the stack; I use it daily for ops scripts and validation."),
    ("sql", "SQL for reporting and reconciliation is part of my current work."),
    ("salesforce", "Salesforce is in the JD; I am deepening there while my core is Excel/VBA and Python around the CRM."),
    ("hubspot", "HubSpot shows up in the role; my strength is systems and automation around the GTM stack."),
    ("revops", "RevOps is the lane I am targeting and matches my recent work."),
    ("revenue operations", "Revenue operations is the lane I am targeting and matches my recent work."),
    ("business systems", "Business systems work is where I have the clearest proof points."),
    ("product ops", "Product ops lines up with how I operate: ship tools, not tickets."),
    ("ai ", "You reference AI; I already use LLMs in production ops, not experiments only."),
    ("machine learning", "I use LLMs and automation in ops; happy to go deeper on ML-adjacent workflows."),
    ("cross-functional", "Cross-functional delivery between ops, finance, and client teams is my norm."),
    ("deal desk", "Deal desk style guardrails and triage are close to my current role."),
    ("implementation", "Implementation and rollout work maps directly to what I have done."),
    ("onboarding", "Client onboarding and rollout are work I have done hands-on."),
    ("integrations", "Integrations and data handoffs are a big part of what I automate."),
    ("excel", "Heavy Excel/VBA is still a strength when the business runs on spreadsheets."),
    ("stakeholder", "Stakeholder-facing ops with technical depth is how I work."),
    ("process", "Process design and improvement are core to what I would own here."),
    ("reporting", "Reporting and validation loops are work I have automated end to end."),
    ("saas", "SaaS ops rhythm (releases, configs, client variance) is familiar territory."),
]

ROLE_SECTION_MARKERS = [
    "what you'll do",
    "what you will do",
    "what we're looking for",
    "what we are looking for",
    "about the role",
    "responsibilities",
    "the role",
    "you will",
]


def clean_jd_text(description: str) -> str:
    t = re.sub(r"<[^>]+>", " ", description or "")
    t = html.unescape(t)
    return re.sub(r"\s+", " ", t).strip()


def _clean_jd_text(description: str) -> str:
    return clean_jd_text(description)


def _jd_hooks(description: str, limit: int = 2) -> list[str]:
    d = _clean_jd_text(description).lower()
    hits: list[str] = []
    for key, line in JD_HOOKS:
        if key in d and line not in hits:
            hits.append(line)
        if len(hits) >= limit:
            break
    if not hits:
        hits.append("I want builder-heavy ops work: systems and automation, not manual processing.")
    return hits


def _jd_focus_sentence(description: str, title: str) -> str:
    """One sentence tied to JD wording (not generic)."""
    text = _clean_jd_text(description)
    if not text:
        return f"For {title}, I would focus on shipping reliable ops systems and cutting manual handoffs."
    lower = text.lower()
    for marker in ROLE_SECTION_MARKERS:
        idx = lower.find(marker)
        if idx == -1:
            continue
        chunk = text[idx : idx + 500]
        chunk = re.sub(r"^[^.]*?(?:what you|about the|responsibilities)[^.]*\.\s*", "", chunk, flags=re.I)
        sentences = re.split(r"(?<=[.!?])\s+", chunk)
        for sent in sentences:
            s = sent.strip()
            if len(s) < 50 or len(s) > 220:
                continue
            low = s.lower()
            if any(
                x in low
                for x in (
                    "equal opportunity",
                    "privacy policy",
                    "accommodation",
                    "we believe",
                    "our mission",
                    "unite humans",
                    "fan-first",
                )
            ):
                continue
            return s[0].upper() + s[1:] if s else s
    for sent in re.split(r"(?<=[.!?])\s+", text):
        s = sent.strip()
        if 50 <= len(s) <= 200 and not any(x in s.lower() for x in ("we believe", "our mission")):
            return s
    return f"For {title}, I would focus on shipping reliable ops systems and cutting manual handoffs."


def build_cover_blurb(
    *,
    company: str,
    title: str,
    description: str,
    config: dict | None = None,
) -> str:
    """Application cover letter (~140-200 words), unique to JD hooks."""
    config = config or load_config()
    sender = config.get("sender_name", "Miles Johnson")
    proof = config.get("proof_line", "").strip()
    hooks = _jd_hooks(description, limit=2)
    focus = _jd_focus_sentence(description, title)
    github = config.get("github", "https://github.com/miles5g")
    loc = "Remote US or Santa Monica hybrid works for me."

    parts = [
        f"Hi {company} team,",
        "",
        f"I am {sender}, applying for {title}. {hooks[0]}",
        "",
    ]
    if len(hooks) > 1:
        parts += [hooks[1], ""]
    parts += [
        focus,
        "",
        proof,
        "",
        f"{loc} GitHub: {github}.",
        "",
        "Thanks,",
        sender,
    ]
    return "\n".join(parts)


def apply_pack_copy_sections(
    *,
    company: str,
    title: str,
    role_url: str,
    description: str,
    config: dict | None = None,
    school_arg: str | None = None,
) -> list[str]:
    """Cover letter + one alumni connection note for job_hunt_apply_pack.md."""
    config = config or load_config()
    lines = [
        "**Cover letter**",
        "",
        build_cover_blurb(company=company, title=title, description=description, config=config),
        "",
    ]
    from linkedin_outreach import apply_pack_outreach_block

    lines.extend(
        apply_pack_outreach_block(
            company=company,
            title=title,
            role_url=role_url,
            config=config,
            school_arg=school_arg,
        )
    )
    return lines
