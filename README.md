# ouroboroswhite: Cybersecurity Portfolio

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
**Last synced:** 2026-08-01 16:31 UTC

<div align="center">

<table>
<tr>
<td align="center">&nbsp;<strong>Rooms Completed</strong>&nbsp;<br>57</td>
<td align="center">&nbsp;<strong>Badges Earned</strong>&nbsp;<br>8</td>
<td align="center">&nbsp;<strong>🟡 Medium</strong>&nbsp;<br>1</td>
<td align="center">&nbsp;<strong>🟢 Easy</strong>&nbsp;<br>44</td>
<td align="center">&nbsp;<strong>ℹ️ Info</strong>&nbsp;<br>12</td>
</tr>
</table>

</div>

<div align="center"><strong>Recent badges</strong></div>

<div align="center">

<table>
<tr>
<td align="center" width="130">
<a href="https://tryhackme.com/p/ouroboroswhite">
<img src="https://assets.tryhackme.com/img/badges/streak7.png" alt="7 Day Streak" width="90"><br>
<strong>7 Day Streak</strong>
</a>
<br><sub>2026-07-23 · common (17.2%)</sub>
</td>
<td align="center" width="130">
<a href="https://tryhackme.com/p/ouroboroswhite">
<img src="https://assets.tryhackme.com/img/badges/linux.png" alt="cat linux.txt" width="90"><br>
<strong>cat linux.txt</strong>
</a>
<br><sub>2026-07-22 · common (28.2%)</sub>
</td>
<td align="center" width="130">
<a href="https://tryhackme.com/p/ouroboroswhite">
<img src="https://assets.tryhackme.com/img/badges/howthewebworks.png" alt="World Wide Web" width="90"><br>
<strong>World Wide Web</strong>
</a>
<br><sub>2026-07-21 · common (17.1%)</sub>
</td>
<td align="center" width="130">
<a href="https://tryhackme.com/p/ouroboroswhite">
<img src="https://assets.tryhackme.com/img/badges/webbed.png" alt="Webbed" width="90"><br>
<strong>Webbed</strong>
</a>
<br><sub>2026-07-21 · common (21.4%)</sub>
</td>
<td align="center" width="130">
<a href="https://tryhackme.com/p/ouroboroswhite">
<img src="https://assets.tryhackme.com/img/badges/networkfundamentals.png" alt="Networking Nerd" width="90"><br>
<strong>Networking Nerd</strong>
</a>
<br><sub>2026-07-21 · common (15.5%)</sub>
</td>
</tr>
</table>

</div>

Full room-by-room history and badge log: [TRAINING.md](TRAINING.md)
<!--THM:END-->

## Study & Knowledge

Formal training: **Level 2 Award in Cybersecurity** (completed), **Level 3 in
progress**, alongside self-directed labs.

For a domain-by-domain summary of what I understand and can apply, see
[FOUNDATIONS.md](FOUNDATIONS.md): threats and vulnerabilities, access control,
defensive measures, offensive security, and UK security law.

## Write-ups

Short accounts of challenge rooms I solved myself, focused on the reasoning and
the security lesson rather than the step-by-step commands. See
[writeups/](writeups/).

## Sample Report

A full-format security assessment report written to professional structure
(executive summary, scope and rules of engagement, methodology, CVSS-rated
findings, and a remediation roadmap), built from lab targets I compromised and
clearly labelled as a lab-based assessment:
[Security Assessment Report](reports/lab-assessment-2026-08.md).

## Projects

### Portfolio Sync Automation

_Python · this repository_

The automation behind this portfolio. It pulls my TryHackMe room and badge
history, renders it into `README.md` and `TRAINING.md`, and publishes the
result on a schedule, without ever committing anything that shouldn't be
public.

The interesting parts are the failure cases rather than the happy path:

- **It fails safe.** If the fetch fails, the previous data file is left
  untouched. A bad sync skips the update; it never publishes an empty
  portfolio over a good one.
- **It tells apart two things that look identical.** TryHackMe's API sits
  behind a bot-protection firewall that answers with HTTP 429, the same
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
  and "authentication"; a check that fires on every run is a check
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
