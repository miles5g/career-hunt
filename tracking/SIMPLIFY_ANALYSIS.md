# Simplify tracker analysis (export 2026-05-20)

**84 roles tracked** · **76 applied** · **8 saved** · ~3 duplicate rows (same company/title)

Data lives in:
- `simplify_export_2026-05-20.csv` (archive)
- `applications.csv` (master tracker)
- `simplify_jobs_full.csv` (same data, backup)

---

## What you did well

- **Right lane:** Heavy RevOps / BizOps / Strategy & Ops — matches your pivot.
- **Real companies:** Discord, OpenAI, Airbnb, Stripe, Activision (Santa Monica), Corner Health (Santa Monica), ZipRecruiter (Santa Monica), ElevenLabs, Backblaze, Hopper, Owner.com, Numeric, Vannevar Labs.
- **Direct ATS links:** Many Ashby/Greenhouse apps (better than LinkedIn-only) — OpenAI, Discord, Dandy, Whatnot, ElevenLabs, Numeric.

---

## Problems hurting response rate

### 1. Volume without tailoring (76 apps in ~3 weeks)

Cold benchmark: **3–8%** screen rate. You need **quality** now that LinkedIn is being fixed — not another 20-app week.

### 2. Stretch / lottery applications (low win probability)

| Company | Role | Issue |
|---------|------|--------|
| OpenAI | GTM Strategy & Ops (2 roles) | Extreme competition |
| Google | YouTube Ads Strategy & Ops | Saved — good instinct to pause |
| Stripe | 5+ different roles in one week | Spray pattern |
| Discord | Strategy & Ops Manager | Stretch without gaming ops background on profile |
| Activision | Data Analytics Engineer | Technical bar high |

**Keep as shots** — but don't expect returns; follow up only if you custom-tailored.

### 3. Likely low-quality / spam postings

| Company | Flag |
|---------|------|
| Jobgether | Aggregator / repost — "Director RevOps" |
| CapitexAI | **4 applications** — same company, vague listings |
| Fuworx Innovations | Obscure company, "Product Data Growth" |
| Great Value Hiring | Generic consultant posting |
| Mobiusengine.ai | Unknown |
| AIIS-Tech | Vague "Digital Operations" |
| RevOpsAI | Fractional |

### 4. Duplicates

- **Synack** — Revops Systems Lead applied **3×** (May 5, 6, 12)
- **CapitexAI** — 4 separate applications
- **Raintree Systems** — 2 titles

### 5. Wrong-fit titles you still applied

- **Business Development Associate** (CloudKitchens) — sales-adjacent
- **Data Analyst** (HopSkipDrive) — analyst grind unless automation-heavy
- **Management Consultant** — often generic pipeline work

### 6. Location mismatches

- Dandy — Mexico Remote (verify US eligibility)
- Wayflyer — Dublin/London
- Ashby GTM role — Canada
- Several Atlanta/Dallas/NYC-only without remote

---

## Tier list (what to prioritize for follow-up)

### Tier 1 — Follow up if you used a direct ATS link (email recruiter / LinkedIn)

| Company | Role | Why |
|---------|------|-----|
| Corner Health | Strategy & Ops Lead | Santa Monica, healthcare startup |
| ZipRecruiter | Sr RevOps BA | Santa Monica |
| Later / Paragon | RevOps Manager | LA / remote OK |
| Backblaze | Product Ops Manager | Remote, SaaS |
| CRAFTSMAN+ | Production Ops (AI & Automation) | Title matches builder story |
| ElevenLabs | Deployment Strategist | LA listed, implementation-adjacent |
| Numeric | Founding BizOps & Strategy | Startup, founding ops |
| Vannevar Labs | Strategy & Business Ops Lead | Remote US |
| ActiveCampaign | Strategy & BizOps Manager | SaaS |
| Implementation Specialist | White Cup | B2B SaaS CRM — lane A fit |
| Seamless.AI | GTM Automation Engineer | Automation in title |

### Tier 2 — Good but competitive

Discord, OpenAI, Stripe (pick **one** role only), Airbnb, Hopper, Owner.com, Whatnot, Activision, SeatGeek, Unstructured GTM Engineer.

### Tier 3 — Deprioritize / don't follow up

CapitexAI, Jobgether, staffing-heavy posts, duplicate Synack apps, consultant/fractional unless you're consulting.

---

## Lane breakdown (from titles)

| Lane | Count (approx) |
|------|----------------|
| C — BizOps / RevOps / Strategy | ~55 |
| B — Automation / systems | ~12 |
| A — Implementation / TAM | ~8 |
| Other / mixed | ~9 |

You're **over-indexed on RevOps** vs **Implementation** and **Automation** where your resume is strongest today.

---

## Recommended next 2 weeks

1. **Stop new Easy Apply bursts** until LinkedIn rewrite is live (see `linkedin/PHASE_1_LINKEDIN.md`).
2. **Cap at 5 apps/week**, all scored ≥18 on rubric.
3. **Follow up Tier 1 only** (10 companies max) — short LinkedIn note referencing specific role + one automation win.
4. **One Stripe role** if any — not five.
5. **Re-apply saved with intention:** Owner.com Strategic Ops Lead, Google (only if resume is tailored), Activision/Xbox associate role with gaming angle in cover line.

---

## Scripts

```powershell
# Re-import after new Simplify export
.\scripts\import_simplify_csv.ps1 -InputCsv "$env:USERPROFILE\Downloads\Simplify_Tracked_Jobs_YYYY-MM-DD.csv"
```

---

## Gaming lane (your interest)

| Company | Role | Status |
|---------|------|--------|
| Discord | Strategy & Ops Manager | Applied May 6 |
| Activision-Blizzard | Data Analytics Engineer | Applied Apr 22 — **Santa Monica** |
| Xbox / External | Associate Studio Strategy | Saved Apr 22 |

**Action:** Add one line in LinkedIn About: "Interested in live ops / game economy / product ops in gaming." Apply to 1 gaming role per week max with custom cover mentioning Godot side projects.
