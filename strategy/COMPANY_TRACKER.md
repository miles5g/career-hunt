# Company career-site tracker (automated)

Direct-to-careers-page job hunting that skips LinkedIn Easy Apply and the recruiter black hole. The agent runs the poller for you. You never touch a terminal.

## How it works

1. `scripts/target_companies.json` is the company list (source of truth, **~75 ATS boards**), split into tiers:
   - `dream_gaming`: Riot, Discord, Roblox, Scopely (+ manual: Xbox, EA, Rockstar, Activision, Epic, PlayStation)
   - `dream_tech`: Anthropic, Scale AI, Databricks, Figma, Airbnb, Coinbase, Robinhood, Affirm, Dropbox, Pinterest, Netflix, NVIDIA
   - `high_odds`: Brex, Plaid, Gusto, Samsara, SoFi, Chime, Mercury, Vanta, Vercel
2. `scripts/find_jobs.py` polls each company's ATS (Greenhouse / Lever / Ashby / SmartRecruiters public JSON APIs), filters to ops/bizops/implementation IC roles, **keeps only US-remote or LA-area hybrid** (drops SF/NYC hybrid, 3+ day RTO, non-LA onsite), scores each against the rubric, dedupes multi-location posts, and writes a ranked report.
3. Output lands in `tracking/job_hunt_results.md` (readable) and `tracking/job_hunt_results.csv` (importable into `tracking/applications.csv`).

## How to run it (just ask the agent)

Say any of:
- **"run the job hunt"** or **"fresh list"** → actionable scan (target **10** roles); **hides only postings** in `tracking/agent_suggested.json` (log with `log_agent_suggestion.py` after you apply). **All boards stay polled.**
- **Simplify sync:** export CSV from dashboard → `python scripts/sync_simplify.py` (see `tracking/SIMPLIFY_IMPORT.md`). No live API; ~weekly export is the practical "sync."
- After you apply to a **pasted** role the agent scored (e.g. Lob on Wellfound), agent logs it in `agent_suggested.json` (or run `python scripts/log_agent_suggestion.py --company Lob --title "..."`).
- **"run the job hunt, fresh only"** → `--days 7`
- **"run high odds only"** → `--tier high_odds`
- **"run the gaming scan"** → `--tier dream_gaming`

Under the hood the agent runs:

```bash
python scripts/find_jobs.py --days 30 --min-score 16 --top 12
```

## What you get each run

| File | Contents |
|------|----------|
| `tracking/job_hunt_apply_pack.md` | Top 6 with resume pick, reality check, copy-paste cover letter |
| `tracking/job_hunt_results.md` | Summary table + manual watchlist links |
| `tracking/job_hunt_results.csv` | Importable list for `applications.csv` |

## Recommendation tiers in the output

- **APPLY**: IC fit. Cover letter included when JD text is available from ATS.
- **MAYBE (score >= 19 only)**: upper-band senior stretch. Included only if score clears 19; still read reality check.
- **Excluded automatically:** STRETCH, MAYBE/senior manager titles, 4+ year JD traps, CS-heavy implementation, comp topping at $100k only, non-remote/non-LA hybrid, duplicate company rows.
- **Apply pack:** APPLY only, score >= 20, no obvious stretches (see skipped section in results).

## Cover letter rule

Letters are written from ATS job text when the API returns enough detail. If a role says `[needs full JD]` or you want form-specific answers, paste the full posting and say **"score and prep [company]"**. Do not use generic letters without reading the JD first.

## Adding or fixing companies

- To add a company: give the agent the careers URL. The agent identifies the ATS, finds the board slug, and adds it to `target_companies.json`.
- "Could not fetch" = wrong slug. Tell the agent to re-probe it. Ashby endpoints are occasionally flaky; a re-run usually fixes it.
- Big companies on Workday/custom boards (Microsoft, NVIDIA, EA, Rockstar, Activision, Epic, PlayStation) have no clean API. They live in the `manual` list and the report prints a pre-filtered search link to check by hand.

## Why this beats spray-and-pray

- You apply on the company site, not through an aggregator. Faster review, no Simplify/Easy-Apply penalty.
- The list is curated to companies you actually want, not whatever the LinkedIn algorithm serves.
- The tool itself is portfolio signal: "I built a poller that monitors 30+ career sites and scores roles against my fit rubric."

## Meta strategies layered on top

1. **Funding triggers**: companies that just raised Series A/B hire their first BizOps/Ops person within months. Add them here when you spot a raise.
2. **First-ops-hire targeting**: 15-80 person companies, well funded, zero existing ops titles on LinkedIn. They need a generalist builder now.
3. **Referral layer**: every role in `job_hunt_apply_pack.md` includes LinkedIn alumni + recruiter copy (see `strategy/LINKEDIN_OUTREACH.md`). Send alumni note before you apply.
4. **Founder direct outreach** (sub-50-person companies): DM the founder/COO with one concrete automation you'd build in week one. Skips the queue.
