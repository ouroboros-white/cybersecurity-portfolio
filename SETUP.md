# Setup

## 1. Add your TryHackMe username as a repo variable

No hidden IDs needed — the endpoints work off your plain public username.

In your new repo on GitHub:

- Go to **Settings → Secrets and variables → Actions → Variables** tab
- Add a variable:
  - Name: `THM_USERNAME`
  - Value: `ouroboroswhite`

## 2. Push this project

```bash
git init
git add .
git commit -m "Initial portfolio sync setup"
git branch -M main
git remote add origin https://github.com/ouroboros-white/<your-repo-name>.git
git push -u origin main
```

## 3. Run it — locally on a schedule, not GitHub Actions

TryHackMe's API sits behind a Vercel bot-protection firewall that
consistently challenge-blocks requests coming from GitHub Actions'
datacenter IPs (you'll see `X-Vercel-Mitigated: challenge` in the response
headers). Retrying doesn't help — it's a JS/browser challenge, not a plain
rate limit. So instead of the GitHub Actions cron, the sync runs from a
Windows Scheduled Task on your own machine, where the request comes from
your home IP.

- `scripts/sync_local.ps1` runs the fetch + render + commit + push in one go.
- Set it up as a daily Scheduled Task. Run this from the repository root in
  PowerShell — `$PWD` fills in the path, so there is no machine-specific
  path to paste (or to publish):

  ```powershell
  schtasks /create /tn "THM Portfolio Sync" /sc daily /st 07:00 /tr "powershell.exe -NoProfile -ExecutionPolicy Bypass -File `"$PWD\scripts\sync_local.ps1`""
  ```

  (Only runs when your PC is on and awake at that time. Adjust `/st` for a
  different time, or use Task Scheduler's GUI if you'd rather configure
  retries/wake-the-PC options.)

- To run it manually any time: `powershell -File scripts\sync_local.ps1`
- To sync and commit without pushing: add `-NoPush`.
- The `.github/workflows/update-portfolio.yml` workflow is kept as a manual
  (`workflow_dispatch`) fallback you can try from the Actions tab, but
  expect it to hit the same bot-challenge block.

## What the sync actually does

1. `fetch_thm.py` — pulls rooms and badges into `data/thm_data.json`. If the
   fetch fails, the previous file is left untouched rather than emptied.
2. `render_portfolio.py` — writes the compact snapshot into `README.md` and
   the full history into `TRAINING.md`, only between the `<!--THM:START-->`
   and `<!--THM:END-->` markers.
3. `safety_check.py` — refuses to publish if the output contains credentials,
   tokens, private keys, CTF flags, email addresses, or local user paths.
   A non-zero exit here aborts the whole sync before anything is committed.
4. Commit and push, staging an explicit allow-list of files only
   (`README.md`, `TRAINING.md`, `data/thm_data.json`) so a stray file in the
   working tree can never be swept into a public commit.

## If the home-IP approach ever gets blocked too

The remaining option is an authenticated browser session (Playwright): a
real browser window opens, you log in yourself once, and the saved session
is reused for later syncs. That is how some similar portfolios do it. Be
aware of the trade-off before adopting it — saved sessions expire, and when
one does, an unattended scheduled task will fail until you log in again by
hand. It converts this from "runs by itself" into "runs when you click it".

## Notes

- The TryHackMe endpoints used here are unofficial — they're the same calls
  your browser makes on a public profile page, not a documented, stable API.
  They could change on you. The fetch script is written so a failed sync
  never wipes your existing data — it just skips the update and logs a
  warning.
- Keep the schedule reasonable (daily is plenty) so you're not hammering
  TryHackMe's servers.
- Everything outside the `<!--THM:START-->` / `<!--THM:END-->` markers in
  `README.md` is yours to edit freely and will never be touched by the
  scripts.
