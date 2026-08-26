# Career job hunt

Command center for job search. **Start with onboarding once**, then run the poller.

## Quick start

```powershell
# 1) Build your profile (resume first, then interests, comp, location, personality)
python scripts/job_hunt.py onboard

# 2) Poll company career sites + ranked apply pack
python scripts/job_hunt.py run

# 3) After Simplify applies: export CSV from dashboard, then
python scripts/job_hunt.py sync
```

In Cursor you can say **"run the job hunt"** or **"fresh list"** after onboarding.

Optional PDF resumes: `pip install pypdf`

## What onboarding does

One question at a time (no multi-tab forms):

1. Resume file or paste
2. Contact links
3. Location (remote US, hybrid cities, cities to skip)
4. Salary floor and target range
5. Detailed **interests** and **disinterests**
6. Short work-style questions + follow-ups based on your answers
7. Writes `context/job_hunt_profile.json` and `context/USER_CONTEXT.md` (local, gitignored)

The poller uses your profile to boost/penalize scores and enforce your comp floor.

## Outputs

| File | What it is |
|------|------------|
| `tracking/job_hunt_apply_pack.md` | Top roles: score, comp, cover letter, one alumni note |
| `tracking/job_hunt_results.md` | Full ranked list |
| `tracking/job_hunt_results.csv` | Spreadsheet export |

## More commands

```powershell
python scripts/job_hunt.py run --days 45 --top 10 --school "Penn State"
python scripts/job_hunt.py score --file jd.txt
python scripts/score_job_listing.py
python scripts/log_agent_suggestion.py --company X --title "Y"
```

## Strategy docs

- `strategy/APPLICATION_SCORING.md` — rubric
- `strategy/COMPANY_TRACKER.md` — poller workflow
- `strategy/LINKEDIN_OUTREACH.md` — alumni notes
- `tracking/SIMPLIFY_IMPORT.md` — Simplify CSV sync
- `tracking/LIVE_PIPELINE.md` — phone + laptop outreach status

## Repo layout

- `scripts/job_hunt.py` — main entry
- `scripts/find_jobs.py` — ATS poller
- `scripts/target_companies.json` — company boards
- `context/job_hunt_profile.example.json` — profile template

Private local files (gitignored): `context/USER_CONTEXT.md`, `context/job_hunt_profile.json`, `tracking/applications.csv`, resume PDFs.

## Phone CareerHunt ↔ laptop Career folder

There is no live disk between the phone cloud VM and the laptop. GitHub is the shared folder. Detail: `tracking/FOLDER_SYNC.md`.

```powershell
# laptop, start of a Cursor session
python scripts/job_hunt.py pull
```

- **Laptop:** `Documents\Cursor Projects\Career`
- **Phone:** new cloud agents on **main** after merge
- **Outreach source of truth:** `tracking/LIVE_PIPELINE.md`
- Coach rule: persist new recruiter facts in that file in the same turn, then commit

Private local files still do not sync: `USER_CONTEXT.md`, `job_hunt_profile.json`, `applications.csv`, resume PDFs.
