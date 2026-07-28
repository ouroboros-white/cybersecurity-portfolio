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

## 3. Run it

- It runs automatically every day at 07:00 UTC (edit the cron line in
  `.github/workflows/update-portfolio.yml` to change that).
- To trigger it immediately: go to the **Actions** tab on GitHub →
  "Update portfolio" → **Run workflow**.
- To test locally before pushing:

  ```bash
  pip install -r scripts/requirements.txt
  export THM_USERNAME=ouroboroswhite
  python scripts/fetch_thm.py
  python scripts/render_readme.py
  ```

## Notes

- The TryHackMe endpoints used here are unofficial — they're the same calls
  your browser makes on a public profile page, not a documented, stable API.
  They could change or rate-limit you. The fetch script is written so a
  failed sync never wipes your existing data — it just skips the update
  and logs a warning.
- Keep the schedule reasonable (daily is plenty) so you're not hammering
  TryHackMe's servers.
- Everything outside the `<!--THM:START-->` / `<!--THM:END-->` markers in
  `README.md` is yours to edit freely and will never be touched by the
  scripts.
