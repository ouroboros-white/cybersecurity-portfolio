# sync_local.ps1
#
# Runs the TryHackMe fetch + README render locally and pushes any changes.
# Intended to be triggered by a Windows Scheduled Task, since TryHackMe's
# Vercel bot-protection firewall consistently blocks requests from GitHub
# Actions' datacenter IPs but not a home connection.

$ErrorActionPreference = "Stop"
$RepoRoot = Split-Path -Parent $PSScriptRoot
Set-Location $RepoRoot

$env:THM_USERNAME = "ouroboroswhite"

python scripts/fetch_thm.py
python scripts/render_readme.py

git add data/thm_data.json README.md
git diff --cached --quiet
if ($LASTEXITCODE -ne 0) {
    git commit -m "chore: sync TryHackMe stats"
    git push
} else {
    Write-Host "No changes to sync."
}
