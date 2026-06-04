#!/usr/bin/env python3
"""
find_jobs.py - Poll company career sites (ATS APIs) for fresh ops/bizops roles,
filter out senior titles, score against Miles's rubric, and rank them.

The agent runs this for you. You do not need to touch a terminal.
Just say "run the job hunt" and the agent executes:

    python scripts/find_jobs.py
    python scripts/find_jobs.py --days 14 --min-score 14
    python scripts/find_jobs.py --tier high_odds
    python scripts/find_jobs.py --tier dream_gaming

Outputs (in tracking/):
    job_hunt_apply_pack.md - top roles to apply (score + location filtered)
    job_hunt_results.md    - full ranked table + skipped stretch roles
    job_hunt_results.csv   - spreadsheet export

Zero dependencies (uses only the Python standard library).
"""

from __future__ import annotations

import argparse
import csv
import html
import json
import re
import sys
import urllib.error
import urllib.request
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
_SCRIPT_DIR = Path(__file__).resolve().parent
if str(_SCRIPT_DIR) not in sys.path:
    sys.path.insert(0, str(_SCRIPT_DIR))
CONFIG_PATH = _SCRIPT_DIR / "target_companies.json"
OUT_CSV = ROOT / "tracking" / "job_hunt_results.csv"
OUT_MD = ROOT / "tracking" / "job_hunt_results.md"
OUT_APPLY = ROOT / "tracking" / "job_hunt_apply_pack.md"
AGENT_SUGGESTED = ROOT / "tracking" / "agent_suggested.json"

# Actionable CSV: APPLY + high MAYBE. Apply pack: strong fits, min 10 when possible.
MAYBE_MIN_SCORE = 18
APPLY_PACK_MIN_SCORE = 17
DEFAULT_TOP_N = 12
APPLY_PACK_MAX_PER_COMPANY = 2
APPLY_PACK_TARGET = 10

# IC "Senior Analyst" is OK; "Senior Manager" / Director is not.
LEVEL_STRETCH_RE = re.compile(
    r"\b((?:senior|sr\.?)\s+)?(manager|director|head of|principal|staff|"
    r"vp|vice president|distinguished)\b|"
    r"\b(lead|director|head of|principal|staff)\s+(?:of|,)?\s*(?:revenue|sales|gtm|ops)",
    re.I,
)

USER_AGENT = "Mozilla/5.0 (job-hunt-poller; personal use)"
TIMEOUT = 12

# --- Rubric keywords (ported from APPLICATION_SCORING.md / score_job_listing.py) ---

TITLE_STRONG = [
    "product operations", "product ops", "business operations", "bizops",
    "revenue operations", "revops", "strategy and operations", "strategy & operations",
    "business systems analyst", "operations analyst", "operations associate",
    "implementation specialist", "implementation consultant", "onboarding specialist",
    "founding operations", "gtm operations", "sales operations analyst",
]

# Generic ops/strategy context words (only count if paired with an IC-level word)
OPS_CONTEXT = [
    "operations", " ops", "business systems", "implementation", "onboarding",
    "strategy", "revops", "revenue operations", "bizops", "gtm",
]
IC_LEVEL = ["associate", "analyst", "specialist", "coordinator", "consultant"]

# Always reject (wrong function entirely)
HARD_EXCLUDE = [
    "engineer", "scientist", "developer", "architect", "attorney", "counsel",
    "nurse", "clinical", "pharmacy", "recruit", "sdr", "account executive",
    "sales development", "mailroom", "data center", "datacenter", "facilit",
    "moderation", "localization", "esports", "influencer", "designer", "design ",
    "quality assurance", "qa analyst", "dei ", "producer", "intern",
]

# Reject for any role (wrong domain for Miles), even if title has a strong phrase
DOMAIN_EXCLUDE = [
    "tax", "compliance", "risk", "fraud", "security", "marketing", "people ",
    "treasury", "collections", "appraisal", "credit", "payroll", "hr ",
    "legal", "privacy", "workplace", "vendor assurance", "social media",
    "talent acquisition", "ta operations", "brokerage", "moderation",
]

# Seniority words that push a role out of Miles's IC lane
SENIOR_WORDS = [
    "director", "vp", "vice president", "head of", "principal", "staff",
    "chief", "sr. manager", "sr manager", "senior manager", "distinguished",
]

COMP_RANGE_RE = re.compile(
    r"\$\s?([\d,]+(?:\.\d+)?)\s*[kK]?\s*(?:-|—|to)\s*\$\s?([\d,]+(?:\.\d+)?)\s*[kK]?",
    re.I,
)
COMP_FLOOR = 100_000


def _parse_dollar(s: str) -> float:
    n = float(s.replace(",", ""))
    if n < 1000:
        n *= 1000
    return n


def _fmt_comp_amount(s: str) -> str:
    n = _parse_dollar(s)
    if n >= 1000:
        return f"${int(round(n / 1000))}k"
    return f"${int(n)}"


def format_compensation(description: str, ashby_comp: dict | None = None) -> str:
    """Human-readable comp from Ashby payload or JD text."""
    if ashby_comp:
        raw = (
            ashby_comp.get("scrapeableCompensationSalarySummary")
            or ashby_comp.get("compensationTierSummary")
        )
        if raw:
            return re.sub(r"[^\x20-\x7E]", "-", str(raw)).strip()
    ranges = COMP_RANGE_RE.findall(description or "")
    if ranges:
        parts = [f"{_fmt_comp_amount(lo)}-{_fmt_comp_amount(hi)}" for lo, hi in ranges[:2]]
        return " / ".join(parts)
    singles = []
    for m in COMP_RE.finditer(description or ""):
        val = m.group(1)
        if val.isdigit():
            singles.append(int(val))
    if singles:
        top = max(singles)
        return f"~${top}k mentioned" if top < 1000 else f"~${int(top / 1000)}k mentioned"
    return "Not listed in ATS"


def comp_floor_ok(description: str, floor: int | None = None) -> bool:
    """Skip roles where the posted salary range tops out below comp floor."""
    floor = floor if floor is not None else COMP_FLOOR
    tops = []
    for low, high in COMP_RANGE_RE.findall(description):
        tops.append(_parse_dollar(high))
    if not tops:
        return True
    return max(tops) >= floor


def jd_requires_years(description: str, minimum: int = 5) -> bool:
    d = description.lower()
    for m in re.finditer(r"(\d+)\s*\+?\s*years", d):
        if int(m.group(1)) >= minimum:
            return True
    for m in re.finditer(r"(\d+)\s*-\s*(\d+)\s*years", d):
        if int(m.group(1)) >= minimum:
            return True
    return False


def comp_tops_at_floor(description: str) -> bool:
    tops = []
    for _low, high in COMP_RANGE_RE.findall(description):
        tops.append(_parse_dollar(high))
    return bool(tops) and max(tops) <= COMP_FLOOR


def cs_heavy_implementation(title: str, description: str) -> bool:
    t, d = title.lower(), description.lower()
    if "implementation" not in t:
        return False
    return any(
        x in d
        for x in [
            "customer success",
            "account management",
            "cs experience",
            "client success",
            "2-4 years of experience in customer",
        ]
    )


def title_is_level_stretch(title: str) -> bool:
    t = title.lower()
    if re.search(
        r"\b(senior|sr\.?)\s+(analyst|associate|specialist|coordinator|consultant|"
        r"operations analyst|revenue operations|business operations)\b",
        t,
    ):
        return False
    # "Lead Business Analyst" is IC; "Lead Generation" / team lead is not
    if re.search(r"\blead\s+(business\s+)?analyst\b", t):
        return False
    if LEVEL_STRETCH_RE.search(title):
        return True
    if re.search(r"\blead\b", t) and not re.search(
        r"\b(associate|analyst|specialist|coordinator)\b", t
    ):
        return True
    return False


def obvious_stretch(title: str, description: str) -> str | None:
    """Human stretch/borderline — excluded from apply pack. None = OK."""
    t = title.lower()
    if title_is_level_stretch(title):
        return "manager/director/lead title (not your lane)"
    if jd_requires_years(description, 5):
        return "JD requires 5+ years"
    if cs_heavy_implementation(title, description):
        return "CS-heavy implementation (career pivot)"
    if comp_tops_at_floor(description):
        return "posted comp tops at $100k floor only"
    if re.search(r"\bstrategy consultant\b", t) or re.search(r"\bai strategy consultant\b", t):
        return "consultant title, weak ops fit"
    if "contractor" in t or "contract)" in t:
        return "contractor role"
    if "gtm specialist" in t and "operations" not in t:
        return "GTM specialist, not ops IC"
    if any(x in t for x in ["protective services", "finance & strategy", "finance and strategy"]):
        return "wrong function"
    if "enterprise implementation" in t:
        return "enterprise IC bar (4+ yrs typical)"
    return None


def is_apply_pack_eligible(r: dict) -> bool:
    if obvious_stretch(r["title"], r.get("description", "")):
        return False
    if r["rec"] == "APPLY" and r["score"] >= APPLY_PACK_MIN_SCORE:
        return True
    if r["rec"] == "MAYBE" and r["score"] >= MAYBE_MIN_SCORE:
        return True
    return False


def sales_grind(title: str, description: str) -> bool:
    t, d = title.lower(), description.lower()
    if "onboarding" in t or "customer operations" in t:
        if any(x in d for x in ["advisory selling", "cross-sell", "quota/kpi", "hourly pay", "/hr"]):
            return True
    return False


US_STATE_RE = re.compile(
    r"\b(AL|AK|AZ|AR|CA|CO|CT|DE|FL|GA|HI|ID|IL|IN|IA|KS|KY|LA|ME|MD|MA|MI|"
    r"MN|MO|MT|NE|NV|NH|NJ|NM|NY|NC|ND|OH|OK|OR|PA|RI|SC|SD|TN|TX|UT|VA|VT|"
    r"WA|WI|WY|DC)\b"
)
US_NAME_SIGNALS = [
    "united states", "usa", "u.s", "remote - us", "remote, us", "remote us",
    "us - united states", "anywhere in the us", "- us;", "us -",
]
FOREIGN_SIGNALS = [
    "india", "spain", "mexico", "qatar", "united kingdom", "france", "brazil",
    "singapore", "germany", "japan", "china", "ireland", "serbia", "poland",
    "australia", "canada", "bangalore", "barcelona", "seville", "london",
    "paris", "tokyo", "shanghai", "berlin", "dublin", "gurugram", "mumbai",
    "bengaluru", "belgrade", "sydney", "toronto", "vancouver", "doha", "haryana",
]

DESC_BUILD = [
    "automation", "automate", "workflow", "python", "sql", "ai ", "llm",
    "cross-functional", "build", "tooling", "integrate", "experiment",
    "process improvement", "dashboards", "systems",
]
DESC_GRIND = [
    "data entry", "ticket queue", "cold call", "accounts payable",
    "accounts receivable", "reconciliation only", "phone support",
]
REMOTE_WORDS = ["remote", "anywhere", "distributed", "work from home"]
# Miles: US-remote only, OR hybrid with office in Santa Monica (not Hawthorne, DTLA, SF, etc.).
SM_HYBRID = ["santa monica"]
# City in loc string without remote → reject (SpaceX Hawthorne, Bastrop, etc.)
ONSITE_CITY_MARKERS = [
    "hawthorne", "bastrop", "redmond", "woodinville", "starbase", "lompoc",
    "cape canaveral", "mcgregor", "chicago", "denver", "miami", "atlanta",
]
NON_LA_OFFICE = [
    "san francisco", "menlo park", "palo alto", "mountain view", "sunnyvale",
    "san jose", "oakland", "berkeley", "fremont", "redwood city", "foster city",
    "new york", "brooklyn", "manhattan", "queens", "seattle", "bellevue",
    "austin", "denver", "chicago", "boston", "cambridge", "miami", "atlanta",
    "dallas", "houston", "phoenix", "portland", "philadelphia", "washington, dc",
    "arlington, va", "carmel, in", "indianapolis", "nashville", "charlotte",
    "pittsburgh", "detroit", "minneapolis", "salt lake city",
]
HEAVY_RTO_RE = re.compile(
    r"(3\s*days?\s*(in[- ]office|on[- ]site|in office)|"
    r"4\s*days?\s*(in[- ]office|on[- ]site)|"
    r"5\s*days?\s*(in[- ]office|on[- ]site)|"
    r"3x\s*/?\s*week|three\s+days\s+per\s+week\s+in\s+(the\s+)?office)",
    re.I,
)
COMP_RE = re.compile(r"\$\s?(\d{2,3})[,\.]?\d{0,3}\s?[kK]?\b")


def http_get(url: str, retries: int = 1) -> bytes | None:
    req = urllib.request.Request(url, headers={"User-Agent": USER_AGENT})
    for attempt in range(retries + 1):
        try:
            with urllib.request.urlopen(req, timeout=TIMEOUT) as resp:
                return resp.read()
        except urllib.error.HTTPError as e:
            if e.code == 404:
                return None  # wrong slug, no point retrying
        except (urllib.error.URLError, TimeoutError, ConnectionError, Exception):
            pass
    return None


def parse_iso(value: str | None) -> datetime | None:
    if not value:
        return None
    v = str(value).strip()
    # epoch millis (Lever)
    if v.isdigit():
        try:
            return datetime.fromtimestamp(int(v) / 1000, tz=timezone.utc)
        except (ValueError, OSError):
            return None
    v = v.replace("Z", "+00:00")
    for fmt in (None,):  # try fromisoformat first
        try:
            dt = datetime.fromisoformat(v)
            if dt.tzinfo is None:
                dt = dt.replace(tzinfo=timezone.utc)
            return dt
        except ValueError:
            pass
    for fmt in ("%Y-%m-%dT%H:%M:%S", "%Y-%m-%d", "%m/%d/%Y"):
        try:
            return datetime.strptime(v[:19], fmt).replace(tzinfo=timezone.utc)
        except ValueError:
            continue
    return None


def days_ago(dt: datetime | None) -> int | None:
    if not dt:
        return None
    return (datetime.now(timezone.utc) - dt).days


# --- ATS fetchers: each returns list of normalized job dicts or None on failure ---


def fetch_greenhouse(slug: str) -> list[dict] | None:
    url = f"https://boards-api.greenhouse.io/v1/boards/{slug}/jobs?content=true"
    raw = http_get(url)
    if not raw:
        return None
    try:
        data = json.loads(raw)
    except json.JSONDecodeError:
        return None
    jobs = []
    for j in data.get("jobs", []):
        loc = (j.get("location") or {}).get("name", "")
        content = j.get("content", "") or ""
        content = re.sub(r"<[^>]+>", " ", content)
        content = html.unescape(content)
        content = re.sub(r"\s+", " ", content).strip()
        jobs.append({
            "title": j.get("title", ""),
            "location": loc,
            "url": j.get("absolute_url", ""),
            "posted": parse_iso(j.get("updated_at")),
            "description": content[:4000],
        })
    return jobs


def fetch_lever(slug: str) -> list[dict] | None:
    url = f"https://api.lever.co/v0/postings/{slug}?mode=json"
    raw = http_get(url)
    if not raw:
        return None
    try:
        data = json.loads(raw)
    except json.JSONDecodeError:
        return None
    if not isinstance(data, list):
        return None
    jobs = []
    for j in data:
        cats = j.get("categories") or {}
        jobs.append({
            "title": j.get("text", ""),
            "location": cats.get("location", ""),
            "url": j.get("hostedUrl", ""),
            "posted": parse_iso(str(j.get("createdAt", ""))),
            "description": (j.get("descriptionPlain") or "")[:4000],
        })
    return jobs


def fetch_ashby(slug: str) -> list[dict] | None:
    url = f"https://api.ashbyhq.com/posting-api/job-board/{slug}?includeCompensation=true"
    raw = http_get(url)
    if not raw:
        return None
    try:
        data = json.loads(raw)
    except json.JSONDecodeError:
        return None
    jobs = []
    for j in data.get("jobs", []):
        loc = j.get("location", "")
        if j.get("isRemote"):
            loc = (loc + " (Remote)").strip()
        desc = (j.get("descriptionPlain") or j.get("description") or "")[:4000]
        comp_obj = j.get("compensation")
        jobs.append({
            "title": j.get("title", ""),
            "location": loc,
            "url": j.get("jobUrl") or j.get("applyUrl", ""),
            "posted": parse_iso(j.get("publishedDate") or j.get("publishedAt")),
            "description": desc,
            "ashby_compensation": comp_obj if isinstance(comp_obj, dict) else None,
        })
    return jobs


def fetch_smartrecruiters(slug: str) -> list[dict] | None:
    url = f"https://api.smartrecruiters.com/v1/companies/{slug}/postings?limit=100"
    raw = http_get(url)
    if not raw:
        return None
    try:
        data = json.loads(raw)
    except json.JSONDecodeError:
        return None
    jobs = []
    for j in data.get("content", []):
        loc = j.get("location") or {}
        loc_str = ", ".join(filter(None, [loc.get("city"), loc.get("region")]))
        if loc.get("remote"):
            loc_str = (loc_str + " (Remote)").strip()
        jobs.append({
            "title": j.get("name", ""),
            "location": loc_str,
            "url": (j.get("ref") or "").replace("api.smartrecruiters.com", "jobs.smartrecruiters.com"),
            "posted": parse_iso(j.get("releasedDate")),
            "description": "",
        })
    return jobs


FETCHERS = {
    "greenhouse": fetch_greenhouse,
    "lever": fetch_lever,
    "ashby": fetch_ashby,
    "smartrecruiters": fetch_smartrecruiters,
}

try:
    from application_copy import apply_pack_copy_sections, clean_jd_text
except ImportError:
    apply_pack_copy_sections = None  # type: ignore
    clean_jd_text = None  # type: ignore

try:
    from profile import (
        comp_floor_usd,
        hybrid_cities as profile_hybrid_cities,
        load_profile,
        preference_adjustment,
        profile_ready,
    )
except ImportError:
    load_profile = None  # type: ignore
    preference_adjustment = None  # type: ignore
    profile_ready = None  # type: ignore
    comp_floor_usd = None  # type: ignore
    profile_hybrid_cities = None  # type: ignore


# --- Filtering + scoring ---


def title_matches(title: str) -> bool:
    t = title.lower()
    if any(x in t for x in HARD_EXCLUDE):
        return False
    if any(x in t for x in DOMAIN_EXCLUDE):
        return False
    # Sales/customer-service onboarding traps (not ops builder roles)
    if "onboarding associate" in t or "customer operations associate" in t:
        return False  # description filter catches sales variants in run()
    if any(x in t for x in TITLE_STRONG):
        return True
    # Generic ops/strategy role: require an IC-level word
    if any(c in t for c in OPS_CONTEXT) and any(l in t for l in IC_LEVEL):
        return True
    return False


def _blob_has_us(blob: str) -> bool:
    return any(s in blob for s in US_NAME_SIGNALS) or bool(US_STATE_RE.search(blob))


def _foreign_country_in_loc(loc: str) -> bool:
    low = loc.lower()
    foreign_markers = [
        "poland", "germany", "india", "spain", "france", "uk", "united kingdom",
        "brazil", "mexico", "singapore", "japan", "china", "ireland", "australia",
        "canada", "serbia", "dublin", "warsaw", "berlin", "toronto", "london",
        "bangalore", "mumbai", "bengaluru", "sydney", "melbourne",
        "estonia", "colombia", "philippines", "vietnam", "argentina", "portugal",
        "netherlands", "sweden", "norway", "denmark", "finland", "switzerland",
        "belgium", "czech", "romania", "hungary", "israel", "taiwan", "korea",
        "new zealand", "south africa", "nigeria", "egypt", "hungary", "latvia",
        "lithuania", "croatia", "greece", "italy", "austria",
    ]
    return any(m in low for m in foreign_markers)


def _has_us_remote_signal(loc: str, blob: str) -> bool:
    """Remote must be US-based, not 'Remote - Estonia' or 'Germany - Remote'."""
    low = loc.lower()
    us_remote_tags = (
        "remote us", "us-remote", "remote - us", "remote, us", "u.s. remote",
        "united states (remote)", "remote u.s", "remote united states",
        "u.s. remote", "remote in the united states", "remote in us",
    )
    if _foreign_country_in_loc(loc):
        if any(t in low for t in us_remote_tags) or any(t in blob for t in us_remote_tags):
            return True
        return False
    if any(w in low for w in REMOTE_WORDS):
        return True
    if any(t in blob for t in us_remote_tags):
        return True
    if "remote" in blob and _blob_has_us(blob) and not _foreign_country_in_loc(loc):
        return True
    return False


def location_classify(
    location: str,
    description: str = "",
    profile: dict | None = None,
) -> str:
    """Return 'remote', 'hybrid_sm', or 'reject'.

    Hard rule: US-remote OK. Hybrid only if profile/Santa Monica allowlist.
    No SF/NYC/Seattle hybrid, no 3+ days in-office, no non-US-only posts.
    """
    loc = (location or "").strip()
    low = loc.lower()
    blob = f"{loc} {(description or '')[:8000]}".lower()
    hybrid_allow = list(SM_HYBRID)
    if profile and profile_hybrid_cities:
        hybrid_allow.extend(profile_hybrid_cities(profile))
    hybrid_allow = list(dict.fromkeys(hybrid_allow))
    if profile:
        for city in (profile.get("location") or {}).get("exclude_cities") or []:
            if city and city in low:
                if not _has_us_remote_signal(loc, blob):
                    return "reject"
            if city and city in blob and "hybrid" in blob and not _has_us_remote_signal(loc, blob):
                return "reject"

    if HEAVY_RTO_RE.search(blob):
        return "reject"
    for phrase in (
        "5 days a week in office",
        "5 days in-office",
        "5 days in office",
        "five days per week in the office",
        "fully on-site",
        "fully onsite",
    ):
        if phrase in blob:
            return "reject"

    if _foreign_country_in_loc(loc) and not _has_us_remote_signal(loc, blob):
        return "reject"

    if "canada" in low and "united states" not in blob and "remote us" not in blob:
        return "reject"

    has_remote = _has_us_remote_signal(loc, blob)
    in_sm = any(s in low for s in hybrid_allow) or (
        any(s in blob for s in hybrid_allow) and ("hybrid" in blob or any(s in low for s in hybrid_allow))
    )
    non_la_hit = [c for c in NON_LA_OFFICE if c in blob]
    onsite_in_loc = [c for c in ONSITE_CITY_MARKERS + NON_LA_OFFICE if c in low]

    # Listed office city with no US-remote signal (e.g. Hawthorne CA, Bastrop TX)
    if onsite_in_loc and not has_remote:
        return "reject"

    # Non-SM office/hybrid without US-remote
    if non_la_hit and not has_remote:
        if "hybrid" in blob:
            return "reject"
        if any(c in low for c in NON_LA_OFFICE):
            return "reject"

    if has_remote:
        # Remote bait + required SF/NYC office cadence (not Santa Monica)
        if non_la_hit and "hybrid" in blob and not in_sm:
            return "reject"
        return "remote"

    if in_sm and ("hybrid" in blob or "santa monica" in low):
        return "hybrid_sm"

    # US city/state listed without remote or Santa Monica
    if US_STATE_RE.search(loc) and not has_remote and not in_sm:
        return "reject"

    if _blob_has_us(blob) and not has_remote and not in_sm:
        return "reject"

    return "reject"


def location_ok(location: str, description: str = "") -> bool:
    return location_classify(location, description) in ("remote", "hybrid_sm")


def score_job(title: str, description: str, location: str) -> tuple[int, str]:
    t = title.lower()
    d = description.lower()
    blob = t + " " + d

    fit = 3
    if any(x in t for x in TITLE_STRONG):
        fit = 5
    elif "analyst" in t or "associate" in t:
        fit = 4
    elif "operations" in t:
        fit = 3

    build_hits = sum(1 for x in DESC_BUILD if x in blob)
    grind_hits = sum(1 for x in DESC_GRIND if x in blob)
    work = 3
    if build_hits >= 3 and grind_hits == 0:
        work = 5
    elif build_hits >= 2:
        work = 4
    elif grind_hits >= 1:
        work = 2

    loc_type = location_classify(location, description)
    if loc_type == "remote":
        culture = 5
    elif loc_type == "hybrid_sm":
        culture = 4
    else:
        culture = 1

    comp = 3
    m = COMP_RE.findall(description)
    if m:
        try:
            top = max(int(x) for x in m if x.isdigit())
            if top >= 110:
                comp = 5
            elif top >= 100:
                comp = 4
            elif top >= 90:
                comp = 3
            else:
                comp = 2
        except ValueError:
            pass

    win = 3
    if any(x in t for x in ["associate", "analyst", "specialist", "coordinator"]):
        win += 1
    if any(x in t for x in SENIOR_WORDS):
        win -= 2
    elif "senior" in t or "sr." in t or "lead" in t or "manager" in t:
        win -= 1
    yrs = re.search(r"(\d+)\+?\s*years", d)
    if yrs:
        n = int(yrs.group(1))
        if n >= 6:
            win -= 2
        elif n >= 5:
            win -= 1
        elif n <= 3:
            win += 1
    win = max(1, min(5, win))

    total = fit + work + culture + comp + win

    # Level-aware recommendation. Miles's lane is IC (associate/analyst/specialist).
    is_exec = any(x in t for x in SENIOR_WORDS)  # director/vp/principal/staff/head/chief
    is_senior = any(x in t for x in ["senior", "sr.", "sr ", " lead", "manager"])
    if is_exec:
        rec = "STRETCH"  # out of lane; surfaced for awareness only
    elif is_senior:
        rec = "MAYBE" if total >= 17 else "SKIP"
    else:
        if total >= 17 and fit >= 3:
            rec = "APPLY"
        elif total >= 15:
            rec = "MAYBE"
        else:
            rec = "SKIP"
    return total, rec


def norm_company(name: str) -> str:
    return re.sub(r"\s+", " ", (name or "").strip().lower())


def norm_title(title: str) -> str:
    return re.sub(r"\s+", " ", (title or "").strip().lower())


def norm_url(url: str) -> str:
    u = (url or "").strip().lower().rstrip("/")
    u = re.sub(r"\?.*$", "", u)
    u = re.sub(r"#.*$", "", u)
    return u


def load_agent_suggestions() -> list[dict]:
    if not AGENT_SUGGESTED.exists():
        return []
    data = json.loads(AGENT_SUGGESTED.read_text(encoding="utf-8"))
    return list(data.get("suggestions") or [])


def role_suggestion_key(company: str, title: str, url: str = "") -> tuple[str, str, str]:
    return (norm_company(company), norm_title(title), norm_url(url))


def is_previously_suggested(role: dict, suggestions: list[dict]) -> bool:
    co, title, url = role_suggestion_key(role["company"], role["title"], role.get("url", ""))
    for s in suggestions:
        s_co, s_title, s_url = role_suggestion_key(
            s.get("company", ""), s.get("title", ""), s.get("url", ""),
        )
        if url and s_url and url == s_url:
            return True
        if co == s_co and title == s_title:
            return True
    return False


def record_agent_suggestions(roles: list[dict]) -> None:
    """Append apply-pack roles so the next run hides only these postings, not whole boards."""
    existing = load_agent_suggestions()
    keys = {
        role_suggestion_key(s.get("company", ""), s.get("title", ""), s.get("url", ""))
        for s in existing
    }
    today = datetime.now().strftime("%Y-%m-%d")
    for r in roles:
        k = role_suggestion_key(r["company"], r["title"], r.get("url", ""))
        if k in keys:
            continue
        existing.append({
            "company": r["company"],
            "title": r["title"],
            "url": r.get("url", ""),
            "suggested_at": today,
        })
        keys.add(k)
    AGENT_SUGGESTED.parent.mkdir(parents=True, exist_ok=True)
    AGENT_SUGGESTED.write_text(
        json.dumps(
            {
                "_comment": "Agent-recommended roles only. Boards stay polled for new postings.",
                "suggestions": existing,
            },
            indent=2,
        )
        + "\n",
        encoding="utf-8",
    )


def is_actionable(rec: str, score: int) -> bool:
    if rec == "STRETCH" or rec == "SKIP":
        return False
    if rec == "APPLY":
        return True
    if rec == "MAYBE":
        return score >= MAYBE_MIN_SCORE
    return False


def resume_variant(title: str) -> str:
    t = title.lower()
    if any(x in t for x in ["implementation", "onboarding", "consultant", "product ops"]):
        return "Product-Implementation"
    return "Ops-Automation"


def run(
    days: int,
    min_score: int,
    tier_filter: str | None,
    top_n: int,
    school: str | None = None,
) -> list[dict]:
    profile = load_profile() if load_profile else None
    if profile and profile_ready and not profile_ready(profile):
        profile = None
    comp_floor = comp_floor_usd(profile) if comp_floor_usd else COMP_FLOOR
    if profile and profile_ready and profile_ready(profile):
        print(f"Profile loaded (comp floor ${comp_floor:,}).\n")

    config = json.loads(CONFIG_PATH.read_text(encoding="utf-8"))
    results = []
    failed = []
    no_match = []

    ats_list = config.get("ats", [])
    if tier_filter:
        ats_list = [c for c in ats_list if c.get("tier") == tier_filter]

    for entry in ats_list:
        fetcher = FETCHERS.get(entry["type"])
        if not fetcher:
            failed.append((entry["company"], f"unknown ATS type '{entry['type']}'"))
            continue
        jobs = fetcher(entry["slug"])
        if jobs is None:
            failed.append((entry["company"], f"could not fetch ({entry['type']}:{entry['slug']}) - check slug"))
            continue

        matched_any = False
        for job in jobs:
            if not title_matches(job["title"]):
                continue
            if sales_grind(job["title"], job["description"]):
                continue
            if not comp_floor_ok(job["description"], comp_floor):
                continue
            loc_type = location_classify(job["location"], job["description"], profile)
            if loc_type == "reject":
                continue
            d = days_ago(job["posted"])
            if d is not None and d > days:
                continue
            total, rec = score_job(job["title"], job["description"], job["location"])
            pref_delta, pref_note = (0, "")
            if preference_adjustment and profile:
                pref_delta, pref_note = preference_adjustment(
                    job["title"], job["description"], profile,
                )
                total = max(0, min(25, total + pref_delta))
            if total < min_score:
                continue
            matched_any = True
            desc = job.get("description", "")[:3000]
            results.append({
                "company": entry["company"],
                "tier": entry.get("tier", ""),
                "title": job["title"],
                "location": job["location"],
                "loc_type": loc_type,
                "url": job["url"],
                "posted_days": d if d is not None else "",
                "score": total,
                "rec": rec,
                "description": desc,
                "compensation": format_compensation(
                    desc, job.get("ashby_compensation"),
                ),
                "pref_note": pref_note,
            })
        if not matched_any:
            no_match.append(entry["company"])

    # Collapse the same role posted across multiple locations (keep best score).
    deduped: dict[tuple[str, str], dict] = {}
    for r in results:
        key = (r["company"], re.sub(r"\s+", " ", r["title"].strip().lower()))
        if key not in deduped or r["score"] > deduped[key]["score"]:
            if key in deduped:
                r["location"] = deduped[key]["location"]
            deduped[key] = r
    results = list(deduped.values())

    results.sort(key=lambda r: (r["score"], -(r["posted_days"] if isinstance(r["posted_days"], int) else 999)), reverse=True)

    actionable = [r for r in results if is_actionable(r["rec"], r["score"])]
    prior_suggestions = load_agent_suggestions()
    already_suggested: list[dict] = []
    if prior_suggestions:
        still_open = []
        for r in actionable:
            if is_previously_suggested(r, prior_suggestions):
                already_suggested.append(r)
            else:
                still_open.append(r)
        actionable = still_open

    # One best role per company in the apply pack (prefer APPLY over MAYBE at same score).
    def pick_key(r: dict) -> tuple:
        rec_pri = 0 if r["rec"] == "APPLY" else 1
        fresh = r["posted_days"] if isinstance(r["posted_days"], int) else 999
        return (r["score"], -rec_pri, -fresh)

    best_by_co: dict[str, list[dict]] = {}
    for r in actionable:
        co = r["company"]
        lst = best_by_co.setdefault(co, [])
        if len(lst) < APPLY_PACK_MAX_PER_COMPANY:
            if not any(x["title"].lower() == r["title"].lower() for x in lst):
                lst.append(r)
        else:
            worst_i = min(range(len(lst)), key=lambda i: pick_key(lst[i]))
            if pick_key(r) > pick_key(lst[worst_i]):
                lst[worst_i] = r
    actionable_unique = sorted(
        [r for roles in best_by_co.values() for r in roles],
        key=pick_key,
        reverse=True,
    )
    for r in actionable:
        r["stretch_reason"] = obvious_stretch(r["title"], r.get("description", ""))
    pack_sorted = sorted(
        [r for r in actionable if is_apply_pack_eligible(r)],
        key=pick_key,
        reverse=True,
    )
    co_count: dict[str, int] = {}
    top = []
    for r in pack_sorted:
        n = co_count.get(r["company"], 0)
        if n >= APPLY_PACK_MAX_PER_COMPANY:
            continue
        top.append(r)
        co_count[r["company"]] = n + 1
        if len(top) >= top_n:
            break

    # Backfill toward APPLY_PACK_TARGET when strict pool is thin (allow borderline; tag in pack)
    goal = max(top_n, APPLY_PACK_TARGET)
    if len(top) < goal:
        in_top = {id(x) for x in top}
        backfill_pool = sorted(
            [r for r in actionable_unique if id(r) not in in_top and r["score"] >= 17],
            key=pick_key,
            reverse=True,
        )
        for r in backfill_pool:
            n = co_count.get(r["company"], 0)
            if n >= APPLY_PACK_MAX_PER_COMPANY:
                continue
            r["pack_tier"] = "stretch" if obvious_stretch(
                r["title"], r.get("description", "")
            ) else "solid"
            top.append(r)
            co_count[r["company"]] = n + 1
            in_top.add(id(r))
            if len(top) >= goal:
                break
    for r in top:
        r.setdefault("pack_tier", "solid")

    skipped = [r for r in actionable if r not in top and is_actionable(r["rec"], r["score"])]

    write_outputs(
        results, actionable_unique, top, skipped, failed, no_match,
        config.get("manual", []), days, min_score, tier_filter,
        already_suggested,
        school=school,
    )
    # Suggestions logged when you apply: scripts/log_agent_suggestion.py
    print_console(
        top, failed, config.get("manual", []), tier_filter,
        len(actionable_unique), len(results), already_suggested,
    )
    return top


def write_outputs(
    results, actionable_unique, top, skipped, failed, no_match, manual, days, min_score, tier_filter,
    already_suggested: list[dict] | None = None,
    school: str | None = None,
):
    already_suggested = already_suggested or []
    OUT_CSV.parent.mkdir(parents=True, exist_ok=True)
    with OUT_CSV.open("w", newline="", encoding="utf-8") as f:
        w = csv.writer(f)
        w.writerow([
            "score", "rec", "company", "tier", "title", "location",
            "compensation", "posted_days_ago", "url", "resume",
        ])
        for r in top:
            w.writerow([
                r["score"], r["rec"], r["company"], r["tier"], r["title"],
                r["location"], r.get("compensation", ""), r["posted_days"],
                r["url"], resume_variant(r["title"]),
            ])

    tier_note = f" Tier: {tier_filter}." if tier_filter else ""
    lines = [
        f"# Job hunt results ({datetime.now().strftime('%Y-%m-%d %H:%M')})",
        "",
        f"Filters: posted <= {days} days, score >= {min_score}. "
        f"**Apply pack:** score >= {APPLY_PACK_MIN_SCORE} (APPLY) or MAYBE >= {MAYBE_MIN_SCORE}, "
        f"remote US or Santa Monica hybrid only, no director/manager/lead stretch / 5+ yr JD / CS-IC pivot.{tier_note}",
        "",
        f"**{len(top)} roles to apply** (from {len(actionable_unique)} actionable; max {APPLY_PACK_MAX_PER_COMPANY} per company).",
        "",
    ]
    if already_suggested:
        lines += [
            f"**Previously suggested:** {len(already_suggested)} posting(s) hidden "
            f"(see `agent_suggested.json`). Boards still scanned for new roles.",
            "",
        ]
        lines += ["## Previously suggested (same posting, excluded from pack)", ""]
        for r in sorted(already_suggested, key=lambda x: -x["score"])[:20]:
            lines.append(f"- **{r['company']}** — {r['title']} ({r['score']}/25)")
        if len(already_suggested) > 20:
            lines.append(f"- …and {len(already_suggested) - 20} more")
        lines.append("")
    if skipped:
        lines += ["## Skipped (stretch / borderline)", ""]
        for r in skipped:
            reason = r.get("stretch_reason") or (
                "MAYBE / low score" if r["rec"] != "APPLY" else f"score {r['score']}"
            )
            lines.append(f"- **{r['company']}** — {r['title']}: {reason}")
        lines.append("")
    if top:
        lines += [
            "| Score | Rec | Company | Title | Comp | Location | Posted | Link |",
            "|-------|-----|---------|-------|------|----------|--------|------|",
        ]
        for r in top:
            posted = f"{r['posted_days']}d ago" if r["posted_days"] != "" else "?"
            comp = (r.get("compensation") or "—").replace("|", "/")
            lines.append(
                f"| {r['score']}/25 | {r['rec']} | {r['company']} | {r['title']} | "
                f"{comp} | {r['location']} | {posted} | [link]({r['url']}) |"
            )
        lines.append("")
        lines.append(
            f"Cover letters + alumni note: `{OUT_APPLY.name}` (generated per role)."
        )
        lines.append("")

    if manual:
        lines += ["## Manual watchlist (no API, check directly)", ""]
        for m in manual:
            lines.append(f"- **{m['company']}** ({m.get('tier','')}): [{m['url']}]({m['url']}) - {m.get('note','')}")
        lines.append("")

    if failed:
        lines += ["## Could not fetch (fix slug in target_companies.json)", ""]
        for company, reason in failed:
            lines.append(f"- {company}: {reason}")
        lines.append("")

    OUT_MD.write_text("\n".join(lines), encoding="utf-8")

    # Apply pack: top roles with JD excerpt for agent cover-letter pass
    skip_note = ""
    if already_suggested:
        n = len({(r["company"], r["title"]) for r in already_suggested})
        skip_note = f"**New since last suggestions:** {n} prior posting(s) hidden. "
    pack = [
        f"# Apply pack ({datetime.now().strftime('%Y-%m-%d %H:%M')})",
        "",
        skip_note
        + "Ranked for your profile when `context/job_hunt_profile.json` exists. "
        "Each role: score line + cover letter + one alumni note. Full JD at Apply link.",
        "",
    ]
    for i, r in enumerate(top, 1):
        posted = f"{r['posted_days']}d ago" if r["posted_days"] != "" else "?"
        desc = (r.get("description") or "").strip()
        pref = f" · {r['pref_note']}" if r.get("pref_note") else ""
        pack += [
            f"---",
            f"## {i}. {r['company']} — {r['title']}",
            "",
            f"**{r['score']}/25** {r['rec']} · {posted} · {r.get('compensation', 'Comp n/a')} · "
            f"{r['location']} · resume `{resume_variant(r['title'])}` · [Apply]({r['url']})",
        ]
        if r.get("pack_tier") == "stretch":
            reason = r.get("stretch_reason") or obvious_stretch(
                r["title"], r.get("description", "")
            )
            pack.append(f"Stretch: {reason}{pref}")
        elif pref:
            pack.append(pref.strip(" · "))
        pack.append("")
        if apply_pack_copy_sections:
            pack.extend(
                apply_pack_copy_sections(
                    company=r["company"],
                    title=r["title"],
                    role_url=r.get("url", ""),
                    description=desc,
                    school_arg=school,
                )
            )
        else:
            pack += [
                "### Cover letter",
                "",
                "*Run from repo root so application_copy imports.*",
                "",
            ]
    if not top:
        pack += [
            "",
            "_No new postings in your lane (remote US or Santa Monica) right now. "
            "Boards are still scanned. Paste Wellfound/LinkedIn roles or check manual watchlist in "
            f"`{OUT_MD.name}`._",
            "",
        ]
    OUT_APPLY.write_text("\n".join(pack), encoding="utf-8")


def print_console(
    top, failed, manual, tier_filter, actionable_count, total_count,
    already_suggested=None,
):
    already_suggested = already_suggested or []
    hide_note = ""
    if already_suggested:
        hide_note = f" · hid {len(already_suggested)} prior agent suggestions"
    print(
        f"\n=== JOB HUNT: {len(top)} top roles (of {actionable_count} actionable, "
        f"{total_count} raw){hide_note} "
        + (f"tier: {tier_filter} " if tier_filter else "")
        + "===\n"
    )
    if already_suggested:
        print("--- Hidden (agent suggested before) ---")
        for r in sorted(already_suggested, key=lambda x: -x["score"])[:10]:
            print(f"    {r['company']} — {r['title']} ({r['score']}/25)")
        if len(already_suggested) > 10:
            print(f"    ... +{len(already_suggested) - 10} more")
        print()
    for r in top:
        posted = f"{r['posted_days']}d" if r["posted_days"] != "" else "?"
        print(f"[{r['score']}/25 {r['rec']}] {r['company']} - {r['title']} "
              f"({r['location']}, {posted})")
        print(f"    {r['url']}")
    if failed:
        print(f"\n--- {len(failed)} companies could not be fetched (slug fix needed) ---")
        for company, reason in failed:
            print(f"    {company}: {reason}")
    if manual:
        print(f"\n--- {len(manual)} manual watchlist companies (check directly) ---")
        for m in manual:
            print(f"    {m['company']}: {m['url']}")
    print(f"\nFull report: {OUT_MD}")
    print(f"Apply pack: {OUT_APPLY}")
    print(f"CSV: {OUT_CSV}\n")


def main() -> None:
    p = argparse.ArgumentParser(description="Poll company ATS APIs for ops/bizops roles.")
    p.add_argument("--days", type=int, default=30, help="Max days since posting (default 30)")
    p.add_argument("--min-score", type=int, default=14, help="Minimum rubric score 0-25 (default 14)")
    p.add_argument("--tier", choices=["dream_gaming", "dream_tech", "high_odds"], default=None,
                   help="Limit to one tier")
    p.add_argument("--top", type=int, default=DEFAULT_TOP_N,
                   help=f"Max roles in apply pack (default {DEFAULT_TOP_N})")
    p.add_argument(
        "--school",
        default=None,
        help="Alumni school for connection note (e.g. UCSB, Penn State). Default: outreach_config primary_school",
    )
    args = p.parse_args()
    run(args.days, args.min_score, args.tier, args.top, school=args.school)


if __name__ == "__main__":
    main()
