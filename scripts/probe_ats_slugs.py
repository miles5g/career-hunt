#!/usr/bin/env python3
"""One-off: probe ATS slugs. Run from Career/: python scripts/probe_ats_slugs.py"""
import json
import urllib.request

UA = "Mozilla/5.0"
ASHBY = [
    "zapier", "retool", "rippling", "navan", "benchling", "ironclad", "gong", "snowflake",
    "plaid", "whatnot", "lob", "dave", "sunbit", "servicetitan", "snap", "checkr",
    "webflow", "airtable", "faire", "shipbob", "doordash", "cohere", "elevenlabs",
    "miro", "clickup", "monday", "smartsheet", "pagerduty", "hashicorp", "cloudflare",
    "1password", "billcom", "bill", "modern-treasury", "warby-parker", "allbirds",
    "sourcegraph", "anduril", "flexport", "lattice", "toast", "instacart", "reddit",
    "block", "openai", "scale", "runway", "windsurf", "anysphere", "figma",
]
LEVER = [
    "zapier", "retool", "rippling", "grammarly", "benchling", "webflow", "gong",
    "ironclad", "servicetitan", "snap", "dave", "sunbit", "miro", "clickup",
    "canva", "netflix", "palantir", "faire", "shipbob", "doordash",
]
GH = [
    "zapier", "retool", "rippling", "navan", "benchling", "ironclad", "gong",
    "snowflake", "plaid", "whatnot", "snap", "dave", "sunbit", "servicetitan",
    "grammarly", "warbyparker", "faire", "shipbob", "doordash", "cohere",
    "mistral", "elevenlabs", "miro", "clickup", "mondaydotcom", "smartsheet",
    "pagerduty", "hashicorp", "cloudflare", "1password", "coursera", "udemy",
    "hims", "ro", "nerdwallet", "billcom", "moderntreasury", "modern",
]


def count(url: str):
    try:
        req = urllib.request.Request(url, headers={"User-Agent": UA})
        with urllib.request.urlopen(req, timeout=10) as r:
            d = json.loads(r.read())
            if isinstance(d, list):
                return len(d)
            if isinstance(d, dict) and "jobs" in d:
                return len(d["jobs"])
            return 1
    except Exception as e:
        return e


for label, slugs, base in [
    ("ashby", ASHBY, "https://api.ashbyhq.com/posting-api/job-board/{s}"),
    ("lever", LEVER, "https://api.lever.co/v0/postings/{s}?mode=json"),
    ("greenhouse", GH, "https://boards-api.greenhouse.io/v1/boards/{s}/jobs"),
]:
    print(f"\n=== {label} ===")
    for s in slugs:
        n = count(base.format(s=s))
        if isinstance(n, int) and n > 0:
            print(f"  {s}: {n}")
