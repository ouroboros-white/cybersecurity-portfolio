# ouroboroswhite — Cybersecurity Portfolio

I am developing practical cybersecurity skills through hands-on labs and
self-directed study. I learn by building and breaking real systems, then
documenting what I find.

<!-- Edit everything in this file freely - only the block below,
     between THM:START and THM:END, gets overwritten automatically. -->

## About Me

TBC

## Training Snapshot

<!--THM:START-->
**Profile:** [ouroboroswhite](https://tryhackme.com/p/ouroboroswhite)  
**Last synced:** 2026-07-28 16:01 UTC

| Rooms completed | Badges earned |
|---|---|
| 45 | 8 |

**Room difficulty:** 🟡 1 medium · 🟢 32 easy · ℹ️ 12 info

**Recent badges:** `7 Day Streak` `cat linux.txt` `World Wide Web` `Webbed` `Networking Nerd`

Full room-by-room history and badge log: [TRAINING.md](TRAINING.md)
<!--THM:END-->

## Projects

### Portfolio Sync Automation

_Python · this repository_

The automation behind this portfolio. It pulls my TryHackMe room and badge
history, renders it into `README.md` and `TRAINING.md`, and publishes the
result on a schedule — without ever committing anything that shouldn't be
public.

The interesting parts are the failure cases rather than the happy path:

- **It fails safe.** If the fetch fails, the previous data file is left
  untouched. A bad sync skips the update; it never publishes an empty
  portfolio over a good one.
- **It tells apart two things that look identical.** TryHackMe's API sits
  behind a bot-protection firewall that answers with HTTP 429 — the same
  status as an ordinary rate limit. A rate limit is worth retrying; a bot
  challenge is not, because no number of retries from a plain HTTP client
  will pass one. The script inspects the response headers to distinguish
  them and stops immediately on the challenge instead of burning its retry
  budget. Diagnosing this is also why the scheduled job runs locally: the
  challenge fires reliably against CI datacenter IP ranges.
- **Nothing is published without passing a safety gate.** A pre-commit
  check blocks credentials, tokens, private keys, CTF flags, email
  addresses, and local filesystem paths. It deliberately matches
  credential-shaped *field names* and secret-shaped *values* rather than
  keywords, because lab titles legitimately contain words like "password"
  and "authentication" — and a check that fires on every run is a check
  people learn to ignore. It was tested against deliberately poisoned data,
  which is how a gap in it was found and closed.
- **Only an explicit allow-list of files is ever staged**, so a stray file
  in the working directory cannot be swept into a public commit.

Documented in [SETUP.md](SETUP.md).

_Built with AI assistance (Claude Code). The design decisions, priorities,
and review were mine._

## Contact

- TryHackMe: [ouroboroswhite](https://tryhackme.com/p/ouroboroswhite)
- GitHub: [ouroboros-white](https://github.com/ouroboros-white)
