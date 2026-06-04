# LinkedIn outreach

Warm intros beat cold apply. Use **before or the same day** you submit.

## Apply pack (default, fast)

`python scripts/find_jobs.py` writes per role:

- **JD-specific cover letter** (application form)
- **One alumni connection note** (same text for every alum at that company; replace `[First name]`; not InMail)
- **Score, posted date, compensation** (when ATS lists it)

School: `primary_school` in `scripts/outreach_config.json` or `python scripts/find_jobs.py --school "Penn State"`.

## Full templates (optional)

For InMail + recruiter backup after no alumni reply:

`python scripts/gen_linkedin_outreach.py --company "Rain" --title "..." --url "..."`

## Workflow

1. **Score the role** (`strategy/APPLICATION_SCORING.md`). Only outreach for APPLY / strong MAYBE.
2. **Find alumni** on LinkedIn (see below).
3. Paste the **connection note** from `job_hunt_apply_pack.md` to several alumni (batch).
4. **Apply** the same day. Log via Simplify sync or `log_agent_suggestion.py`.

## Find alumni on LinkedIn

On the job card, LinkedIn often shows **“X school alumni work here.”** Use that.

| Step | Action |
|------|--------|
| 1 | Company page → **People** → filter **School** = UCSB or Penn State |
| 2 | Prefer titles: operations, revops, bizops, product ops, strategy, business systems |
| 3 | Skip: recruiters, HR, C-suite (unless tiny startup) |
| 4 | 2nd degree > 3rd; mutual connections = higher reply rate |

**Search URL** is auto-built in each outreach file under `tracking/outreach/`.

Schools in `scripts/outreach_config.json`: **UC Santa Barbara**, **Penn State**. Try both before using the recruiter template.

## Scripts

| Script | Purpose |
|--------|---------|
| `scripts/gen_linkedin_outreach.py` | Write `tracking/outreach/{company}-{role}.md` |
| `scripts/linkedin_outreach.py` | Message builders (imported by generator + poller) |
| `scripts/outreach_config.json` | Your name, schools, proof line (edit once) |

### Examples

```powershell
python scripts/gen_linkedin_outreach.py --company Whatnot --title "Strategy and Operations Manager, Revenue Operations" --alumni-first Jordan --school UCSB

python scripts/gen_linkedin_outreach.py --from-pack 1 --stdout
```

The job hunt poller writes outreach into **`tracking/job_hunt_apply_pack.md`** for every role automatically (with the cover letter blurb).

## Voice

- Direct, short, no corporate fluff (see `.cursor/rules/career-coach.mdc`).
- Alumni angle: shared school, **one** proof line (~80% automation), ask for **10 min** or hiring owner.
- Recruiter angle: role link, remote US / Santa Monica question, who owns the req.

## Do not

- Mass InMail blasts
- Pretend you know someone you have not met
- Ask for a referral in the connection request (save for follow-up)
