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
- Set it up as a daily Scheduled Task:

  ```
  schtasks /create /tn "THM Portfolio Sync" /sc daily /st 07:00 /tr "powershell.exe -NoProfile -ExecutionPolicy Bypass -File \"%USERPROFILE%\OneDrive\Desktop\Cybersecurity\thm-portfolio-sync\scripts\sync_local.ps1\""
  ```

  (Only runs when your PC is on and awake at that time. Adjust `/st` for a
  different time, or use Task Scheduler's GUI if you'd rather configure
  retries/wake-the-PC options.)

- To run it manually any time: `powershell -File scripts\sync_local.ps1`
- The `.github/workflows/update-portfolio.yml` workflow is kept as a manual
  (`workflow_dispatch`) fallback you can try from the Actions tab, but
  expect it to hit the same bot-challenge block.

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
