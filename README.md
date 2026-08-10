# ouroboroswhite: Cybersecurity Portfolio

Offensive security lab work, documented to a professional standard: web, cloud,
and Linux systems broken in controlled environments and written up as full
assessment reports with findings, impact, detection, and remediation.

<!-- Edit everything in this file freely - only the block below,
     between THM:START and THM:END, gets overwritten automatically. -->

## About Me

I break web applications, cloud identity, and Linux hosts in lab environments, and
write the results up as client-style assessment reports. I am working toward a
junior penetration testing role, and from there toward independent
**offensive-security** consulting.

I learn by building and breaking real systems and writing up the reasoning, not
just the result. I bring a competitive-performance mindset to it: disciplined
practice, fast iteration, and a habit of reviewing my own mistakes.

**Current focus:** penetration testing and red teaming, backed by enough defensive
understanding to sharpen the offense. I write detection analysis into my own
reports, because knowing how an attack is caught makes it both easier to carry out
and easier to explain to a client.

**Working towards:** CompTIA Security+, then OSCP and CRTO, alongside the TryHackMe
Jr Penetration Tester and SOC Level 1 paths and a Level 3 cyber security
qualification.

**Core skills**

- **Web:** authentication bypass, NoSQL and SQL injection, server-side template
  injection, business-logic and race-condition flaws, broken access control
- **Cloud:** AWS and Azure identity and access abuse, storage and secret-store
  attacks (SAS tokens, service principals, Key Vault)
- **Linux:** exploitation, privilege escalation, post-exploitation, credential
  reuse and lateral movement
- **Tooling:** Burp Suite, Metasploit, nmap, the AWS and Azure CLIs, Python
- **Reporting:** professional assessment reports with CVSS scoring, CWE mapping,
  business impact, detection analysis, and remediation

**Featured assessments**

- [Single-Host Full Compromise](reports/host-compromise-2026-08.md): a web
  application taken to root through a chained attack path.
- [Azure Cloud Attack Chain](reports/cloud-attack-chain-azure-2026-08.md): a
  low-privilege user to a Key Vault secret via a leaked SAS token and a stolen
  service principal.
- [Business-Logic and API Abuse](reports/business-logic-assessment-2026-08.md): a
  reward economy defeated by a race condition.
- [LLM Agent Prompt Injection](reports/llm-agent-prompt-injection-2026-08.md): an AI
  concierge's confused-deputy authorization routed into host command execution.

**Next:** taking Windows and Active Directory to the same depth as the Linux and
cloud work above, and adding each one to this repository as it is done.

## Training Snapshot

<!--THM:START-->
**Profile:** [ouroboroswhite](https://tryhackme.com/p/ouroboroswhite)  
**Last synced:** 2026-08-10 06:00 UTC

<div align="center">

<table>
<tr>
<td align="center">&nbsp;<strong>Rooms Completed</strong>&nbsp;<br>88</td>
<td align="center">&nbsp;<strong>Badges Earned</strong>&nbsp;<br>11</td>
<td align="center">&nbsp;<strong>🟡 Medium</strong>&nbsp;<br>8</td>
<td align="center">&nbsp;<strong>🟢 Easy</strong>&nbsp;<br>67</td>
<td align="center">&nbsp;<strong>ℹ️ Info</strong>&nbsp;<br>13</td>
</tr>
</table>

</div>

<div align="center"><strong>Recent badges</strong></div>

<div align="center">

<table>
<tr>
<td align="center" width="130">
<a href="https://tryhackme.com/p/ouroboroswhite">
<img src="https://assets.tryhackme.com/img/badges/blue.png" alt="Blue" width="90"><br>
<strong>Blue</strong>
</a>
<br><sub>2026-08-03 · rare (8.4%)</sub>
</td>
<td align="center" width="130">
<a href="https://tryhackme.com/p/ouroboroswhite">
<img src="https://assets.tryhackme.com/img/badges/metasploit.png" alt="Metasploitable" width="90"><br>
<strong>Metasploitable</strong>
</a>
<br><sub>2026-08-03 · rare (7.6%)</sub>
</td>
<td align="center" width="130">
<a href="https://tryhackme.com/p/ouroboroswhite">
<strong>Session Held</strong>
</a>
<br><sub>2026-08-03 · rare (1%)</sub>
</td>
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

## Sample Reports

Full-format security assessment reports written to professional structure
(executive summary, scope, methodology, CVSS-rated findings with purple-team
detection analysis, and a remediation roadmap), built from lab targets I
compromised and clearly labelled as lab-based:

- [Web & Cloud Assessment](reports/lab-assessment-2026-08.md): three lab targets,
  isolated findings across web and cloud.
- [Single-Host Full Compromise](reports/host-compromise-2026-08.md): one host
  taken from anonymous to root through a chained attack path.
- [Command-Injection Chain to Root](reports/command-injection-chain-2026-08.md): the
  same injection flaw exploited twice: unauthenticated at the edge, then as root.
- [Business-Logic & API Abuse](reports/business-logic-assessment-2026-08.md): a
  web application defeated by a race condition in its reward logic.
- [Azure Cloud Attack Chain](reports/cloud-attack-chain-azure-2026-08.md): a
  low-privilege Azure user to a Key Vault secret, via a leaked SAS token and a
  stolen service principal.
- [LLM Agent Prompt Injection](reports/llm-agent-prompt-injection-2026-08.md): an
  AI concierge agent whose model-adjudicated tool authorization was bypassed by
  routing a command through an authorized record, reaching host code execution.

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
