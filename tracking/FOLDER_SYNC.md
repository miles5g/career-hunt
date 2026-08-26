# Phone ↔ laptop sync

Cursor Cloud on your phone and Cursor on the laptop **do not share a disk**. OneDrive, iCloud, and a “shared folder” on the PC are invisible to the phone agent VM.

The shared folder is this GitHub repo: **miles5g/career-hunt**.

```
Phone agent  --commit/PR-->  GitHub main  --git pull-->  laptop Career folder
Laptop edits --commit/push->  GitHub main  --new agent-->  next phone session
```

## Daily loop

1. **Laptop, start of session:** `python scripts/job_hunt.py pull`
2. **Phone chat that changes a live thread:** tell the agent to update `tracking/LIVE_PIPELINE.md` (the coach rule already requires this). Merge that PR (or this standing sync PR), then pull on the laptop.
3. **New phone agent:** start it on **main** after merge, not on an old chat’s branch.

Optional Windows (pull when you log in): Task Scheduler → `python` → args `scripts/job_hunt.py pull` → start in `Documents\Cursor Projects\Career`.

## What will never auto-sync

These are gitignored on purpose (public repo):

- `context/USER_CONTEXT.md`
- `context/job_hunt_profile.json`
- `tracking/applications.csv`
- resume PDFs

Phone agents will keep asking you to onboard unless those stay laptop-only. That is expected. Put outreach status in `LIVE_PIPELINE.md` instead.

If you want the phone agent to see your full profile, make this repo **private** and stop gitignoring `USER_CONTEXT.md`. Do not do that while the repo is public.
