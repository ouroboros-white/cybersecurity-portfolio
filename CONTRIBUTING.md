# Repo conventions

Working notes for maintaining this repo. Not part of the portfolio itself.

## Publishing safety

- **No flags or answers.** Never paste a room's flag, answer string, or
  cracked credential, in files or in commit messages. `scripts/safety_check.py`
  blocks curly-brace flag patterns and credential-shaped strings before
  anything is committed, and the pre-commit hook runs it.
- **Check the event first.** For live events with prizes, confirm that solution
  write-ups are permitted before publishing. If unsure, draft now and publish
  after the event closes.
- **Staged paths are allow-listed.** `sync_local.ps1` stages only the generated
  files by name, so a stray file in the working tree cannot be swept into a
  public commit.

## House style

- **No em dashes.** Recast the sentence rather than swapping the character. A
  comma, colon, semicolon, brackets or a full stop is always available, and the
  result usually reads tighter. Check before committing:

  ```bash
  git grep -n '—' -- '*.md'
  ```

  Use `git grep`, not plain `grep -r`. It searches only tracked files, so it
  will not report hits from `study/` and other gitignored paths. Those are
  private notes, and the rule is about published prose.

- **Write-ups follow [writeups/TEMPLATE.md](writeups/TEMPLATE.md)** and must
  carry the full metadata header (title, platform, difficulty, date, tags). The
  index generator reads that header and will fail loudly if it is incomplete.

## Generated sections

Two scripts rewrite marked regions in place. Everything outside the markers is
hand-written and preserved.

| Script | Writes | Markers |
| --- | --- | --- |
| `scripts/render_portfolio.py` | `README.md`, `TRAINING.md` | `<!--THM:START-->` / `<!--THM:END-->` |
| `scripts/render_writeups.py` | `writeups/README.md` | `<!--INDEX:START-->` / `<!--INDEX:END-->` |

Run the whole pipeline with `powershell -File scripts\sync_local.ps1 -NoPush`
to update everything locally without publishing.
