# Phone ↔ laptop sync

Cursor Cloud on your phone and Cursor on the laptop **do not share a disk**. OneDrive, iCloud, and a “shared folder” on the PC are invisible to the phone agent VM.

The shared folder is this GitHub repo: **miles5g/career-hunt**.

```
Phone agent  --commit/PR-->  GitHub main  --git pull-->  laptop Career folder
Laptop edits --commit/push->  GitHub main  --new agent-->  next phone session
```

## What to say

- **Phone:** `push any new info` → agent writes `tracking/LIVE_PIPELINE.md` and lands it on `main`.
- **Laptop:** `pull any new phone info` → `python scripts/job_hunt.py pull`, then read the pipeline.

That is the whole loop. Not automatic. Those two sentences are enough if the phone commit actually reached `main`.

## Daily loop

1. **Laptop, start of session:** say **pull any new phone info** (or run `python scripts/job_hunt.py pull`).
2. **Phone chat that changes a live thread:** say **push any new info**.
3. **New phone agent:** start it on **main**, not an old chat’s branch.

Optional Windows (pull when you log in): Task Scheduler → `python` → args `scripts/job_hunt.py pull` → start in `Documents\Cursor Projects\Career`.

## What will never auto-sync

These are gitignored on purpose (public repo):

- `context/USER_CONTEXT.md`
- `context/job_hunt_profile.json`
- `tracking/applications.csv`
- resume PDFs

Phone agents will keep asking you to onboard unless those stay laptop-only. That is expected. Put outreach status in `LIVE_PIPELINE.md` instead.

If you want the phone agent to see your full profile, make this repo **private** and stop gitignoring `USER_CONTEXT.md`. Do not do that while the repo is public.
