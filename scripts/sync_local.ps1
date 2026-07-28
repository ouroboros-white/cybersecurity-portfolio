# sync_local.ps1
#
# Runs the TryHackMe fetch, renders README.md + TRAINING.md, checks the
# result for anything that must not be published, then commits and pushes.
#
# Intended to be triggered by a Windows Scheduled Task, since TryHackMe's
# Vercel bot-protection firewall consistently blocks requests from GitHub
# Actions' datacenter IPs but not a home connection.
#
# Usage:
#   powershell -File scripts\sync_local.ps1            # sync and push
#   powershell -File scripts\sync_local.ps1 -NoPush    # sync locally only

param(
    [switch]$NoPush
)

$ErrorActionPreference = "Stop"
$RepoRoot = Split-Path -Parent $PSScriptRoot
Set-Location $RepoRoot

$env:THM_USERNAME = "ouroboroswhite"

python scripts/fetch_thm.py
python scripts/render_portfolio.py

# Refuse to publish if anything credential-shaped made it into the output.
python scripts/safety_check.py

# Explicit allow-list: only these paths are ever staged, so a stray file in
# the working tree can never be swept into a public commit by accident.
git add README.md TRAINING.md data/thm_data.json

git diff --cached --quiet
if ($LASTEXITCODE -eq 0) {
    Write-Host "No changes to sync."
    exit 0
}

git commit -m "chore: sync TryHackMe stats"

if ($NoPush) {
    Write-Host "Committed locally. Skipping push (-NoPush)."
} else {
    git push
}
