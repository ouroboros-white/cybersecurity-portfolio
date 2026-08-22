# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## What this repository is

A public cybersecurity portfolio published under the pseudonym **ouroboroswhite**, plus
the Python automation that keeps it current. Most of the repository is prose
(assessment reports, write-ups, detection rules); the code exists to render and
guard that prose. Treat published Markdown with the same care as code: it is the
deliverable.

## Commands

Run everything from the repository root. Dependencies: `pip install -r scripts/requirements.txt`
(just `requests`).

```bash
powershell -File scripts\sync_local.ps1 -NoPush
```

That is the whole pipeline: fetch, render both generated regions, safety check,
stage the allow-list, commit. Drop `-NoPush` to publish. Individual stages:

| Command | Does |
| --- | --- |
| `THM_USERNAME=ouroboroswhite python scripts/fetch_thm.py` | Pulls rooms and badges into `data/thm_data.json`. Fails safe: a failed fetch leaves the old file intact. |
| `python scripts/render_portfolio.py` | Rewrites the `THM` marker regions in `README.md` and `TRAINING.md` from that JSON. |
| `python scripts/render_writeups.py` | Rewrites the `INDEX` marker region in `writeups/README.md` from each write-up's metadata header. |
| `python scripts/safety_check.py` | Scans every git-tracked text file for secrets, flags, emails, and identifying local paths. Non-zero exit aborts the sync. |
| `python scripts/validate_cvss.py` | Recomputes every CVSS score in `reports/` from its own vector. |

There is no test suite and no linter. `safety_check.py` and `validate_cvss.py`
are the checks; run both before committing anything you changed by hand.

The git hook lives in `hooks/`, not `.git/hooks`, and is already wired up via
`git config core.hooksPath hooks`. It runs `validate_cvss.py` only when a report
or the validator itself is staged. If a clone loses that setting, restore it with
the same command.

## Architecture

### The generated-region pattern

Two renderers rewrite marked regions in place and never touch anything outside
them. Hand-written prose and generated content live in the same files by design.

| Script | Writes | Markers |
| --- | --- | --- |
| `scripts/render_portfolio.py` | `README.md`, `TRAINING.md` | `<!--THM:START-->` / `<!--THM:END-->` |
| `scripts/render_writeups.py` | `writeups/README.md` | `<!--INDEX:START-->` / `<!--INDEX:END-->` |

Edit inside a marker region and the next sync silently discards your work.
Removing the markers makes the renderer exit with an error rather than guess.

### Why the sync runs locally, not in CI

TryHackMe's API sits behind a Vercel bot-protection firewall that challenge-blocks
GitHub Actions' datacenter IPs. The challenge answers HTTP 429, the same status as
an ordinary rate limit, so `fetch_thm.py` inspects `X-Vercel-Mitigated: challenge`
and bails immediately instead of spending its retry budget on something no plain
HTTP client can pass. `.github/workflows/update-portfolio.yml` is kept as a manual
`workflow_dispatch` fallback and is expected to fail that way. The real schedule is
a Windows Scheduled Task calling `sync_local.ps1`. See `SETUP.md`.

### Publishing safety, three layers

1. **`.gitignore` excludes `study/`.** Private local notes that must never be
   published. Do not remove that rule. `safety_check.py` cannot cover it: the
   scanner only sees files git already tracks, so an untracked file there is
   invisible right up until a `git add .` publishes it.
2. **`safety_check.py` is the backstop.** It matches credential-shaped JSON *keys*
   and secret-shaped *values*, deliberately not keywords, because room titles
   legitimately contain "password" and "authentication" and a check that fires
   every run is a check people learn to ignore. If a finding is a false positive,
   adjust the patterns deliberately; do not skip the check.
3. **Staging is an explicit allow-list.** Both `sync_local.ps1` and the workflow
   stage `README.md TRAINING.md writeups/README.md data/thm_data.json` by name, so
   a stray file in the working tree cannot be swept into a public commit.

`CONTENT_USERNAMES` in `safety_check.py` allow-lists usernames that are lab
content. Add to it only after confirming the name is room content. Never add a
name in order to silence a finding: that is the finding working as intended.

## Content conventions

- **No flags, answers, or cracked credentials**, in files or in commit messages.
  If one slips into history, rewrite the history.
- **No em dashes.** They read as an AI tell. Recast the sentence rather than
  swapping the character. Check with the command below, which searches tracked
  files only so private notes in `study/` are not reported. It spells the
  character as an escape so this file is not itself a permanent hit:

  ```bash
  git grep -n "$(printf '—')" -- '*.md'
  ```
- **Write-ups** follow `writeups/TEMPLATE.md` and must carry the full metadata
  header (`# Title`, `**Difficulty:**`, `**Date:**`, `**Tags:**`).
  `render_writeups.py` parses that header and raises loudly if it is incomplete.
  Tags drive categorisation via the `CATEGORIES` list, which is ordered most
  specific first, so a write-up lands in the first category it matches.
- **Reports** follow a fixed commercial structure: executive summary with a
  findings-at-a-glance table, scope and rules of engagement with an asset table,
  methodology, attack path with ATT&CK mapping, detailed findings, remediation
  roadmap, conclusion, severity and tooling appendices. Each finding is `F-NN`
  with a metadata table (Severity, CVSS 3.1 score plus vector, CWE, affected
  component, status) followed by CVSS rationale, description, sanitised evidence,
  business impact, **expected detection opportunities**, and remediation. Findings
  are numbered in attack order, not severity order.
- **CVSS scores are validated, not asserted.** `validate_cvss.py` recomputes the
  base score from the vector and cross-checks the severity band and the
  at-a-glance table row. Change a vector and you must change every place the score
  appears.
- **Detection rules** in `detections/` are Sigma YAML written from behaviour
  actually observed during an assessment, each naming the report and finding it
  came from. Conversion limits and untuned thresholds are stated honestly in
  `detections/README.md`; keep that honesty when adding rules.
