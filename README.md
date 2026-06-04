# Career workspace

Miles Johnson — job search command center for Cursor.

## Start here

| File | Purpose |
|------|---------|
| [`context/USER_CONTEXT.md`](context/USER_CONTEXT.md) | Who you are, goals, blacklist — **AI reads first** |
| [`strategy/JOB_SEARCH_STRATEGY.md`](strategy/JOB_SEARCH_STRATEGY.md) | Diagnosis + weekly workflow |
| [`strategy/SAVED_FILTERS.md`](strategy/SAVED_FILTERS.md) | LinkedIn + Wellfound booleans |
| [`wellfound/WELLFOUND_PREFERENCES_CHECKLIST.md`](wellfound/WELLFOUND_PREFERENCES_CHECKLIST.md) | Wellfound alert setup (WF-1/2/3) |
| [`strategy/APPLICATION_SCORING.md`](strategy/APPLICATION_SCORING.md) | 1–5 rubric before applying |
| [`tracking/applications.csv`](tracking/applications.csv) | Application log (84 Simplify jobs imported) |
| [`tracking/SIMPLIFY_ANALYSIS.md`](tracking/SIMPLIFY_ANALYSIS.md) | Application history analysis & tier list |
| [`CAREER_STATUS.md`](CAREER_STATUS.md) | What's done + next steps |
| [`resumes/RESUME_VARIANTS.md`](resumes/RESUME_VARIANTS.md) | 2 PDFs → LinkedIn lanes + Wellfound saves |
| [`plans/PHASE_1_PLAN.md`](plans/PHASE_1_PLAN.md) | Next 2 weeks checklist |
| [`plans/AUTOMATION_ROADMAP.md`](plans/AUTOMATION_ROADMAP.md) | What to automate (and not) |

## Cursor rules

Project rules live in [`.cursor/rules/career-coach.mdc`](.cursor/rules/career-coach.mdc) — loaded automatically in this workspace.

## Job hunt poller (company career sites)

Polls **Greenhouse / Lever / Ashby** boards from `scripts/target_companies.json`, filters to your lane, and writes ranked results.

```powershell
# Windows (full path if `python` is not on PATH)
& "$env:LOCALAPPDATA\Programs\Python\Python311\python.exe" scripts/find_jobs.py --days 30 --min-score 16 --top 12
```

| Output | Purpose |
|--------|---------|
| `tracking/job_hunt_apply_pack.md` | Top roles to apply |
| `tracking/job_hunt_results.md` | Full table + skipped list |
| `tracking/job_hunt_results.csv` | Spreadsheet export |

**Filters:** US remote or LA-area hybrid only; no manager/director stretch; expanded company list (40+ ATS boards). See `strategy/COMPANY_TRACKER.md`.

## LinkedIn outreach (alumni + recruiter backup)

See [`strategy/LINKEDIN_OUTREACH.md`](strategy/LINKEDIN_OUTREACH.md). Generates UCSB/Penn State alumni notes and a recruiter fallback.

```powershell
python scripts/find_jobs.py --days 45 --min-score 16 --top 6
```

Each role in `tracking/job_hunt_apply_pack.md` includes a **cover letter blurb** and **LinkedIn alumni + recruiter** messages. Standalone file: `python scripts/gen_linkedin_outreach.py --company Rain --title "..."`.

## Simplify sync (applied jobs → fresh list)

Simplify has **no public API**. After you apply via Simplify, export CSV from the [dashboard](https://simplify.jobs/dashboard), then:

```powershell
python scripts/sync_simplify.py
```

Merges into `applications.csv` and updates `agent_suggested.json` so the job hunt poller hides roles you already applied to. See `tracking/SIMPLIFY_IMPORT.md`.

## Other scripts

```powershell
python scripts/score_job_listing.py   # score a pasted JD
python scripts/gen_cover_letter_pdf.py tracking/roles/My-Letter.txt
```

## Status

- **Phase 1:** Positioning + process
- **Phase 2:** ATS poller + rubric scoring (active)
- **Phase 3:** Optional browser assist (not mass auto-apply)
