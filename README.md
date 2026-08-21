# ouroboroswhite: Cybersecurity Portfolio

_Offensive security, focused on web application, cloud, and LLM security, working
toward a junior penetration testing role._

Security lab work documented to a professional standard: web applications, cloud
identity, Linux hosts, LLM agents, and recovered devices, broken or examined in
controlled environments and written up as full assessment reports with findings,
impact, detection, and remediation.

> **Every report here is my own work.** Each one documents an assessment I
> personally carried out against intentionally vulnerable lab and training targets
> (primarily TryHackMe), then wrote up to the structure of a commercial
> deliverable. The exploitation, findings, and evidence are mine: not hypothetical
> scenarios, and not reproduced from walkthroughs. These are lab exercises rather
> than authorized client engagements, and target identifiers are redacted as they
> would be in a real report.

<!-- Edit everything in this file freely - only the block below,
     between THM:START and THM:END, gets overwritten automatically. -->

## About Me

I break web applications, cloud identity, Linux hosts, and LLM agents in lab
environments, and write the results up as client-style assessment reports. The
same method applies when the work runs the other way: one of the reports below is
a forensic recovery from a lost device rather than an attack on a live target. I
am working toward a junior penetration testing role, and from there toward
independent **offensive-security** consulting.

I learn by breaking real systems and writing up the reasoning, not
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
- **AI/LLM:** prompt injection, agent tool abuse, model-adjudicated authorization
  flaws, guardrail bypass, mapped to the OWASP Top 10 for LLM Applications
- **Forensics and IR:** offline data-at-rest recovery, Windows registry and LSA
  secrets, DPAPI-protected credential stores, evidential handling of a disk image
- **Tooling:** Burp Suite, Metasploit, nmap, impacket, the AWS and Azure CLIs, Python
- **Reporting:** professional assessment reports with CVSS scoring, CWE mapping,
  business impact, detection analysis, and remediation

**Next:** taking Windows and Active Directory to the same depth as the Linux and
cloud work above, and adding each one to this repository as it is done.

## Training Snapshot

<!--THM:START-->
**Profile:** [ouroboroswhite](https://tryhackme.com/p/ouroboroswhite)  
**Last synced:** 2026-08-21 06:00 UTC

<div align="center">

<table>
<tr>
<td align="center">&nbsp;<strong>Rooms Completed</strong>&nbsp;<br>106</td>
<td align="center">&nbsp;<strong>Badges Earned</strong>&nbsp;<br>15</td>
<td align="center">&nbsp;<strong>🔴 Hard</strong>&nbsp;<br>1</td>
<td align="center">&nbsp;<strong>🟡 Medium</strong>&nbsp;<br>8</td>
<td align="center">&nbsp;<strong>🟢 Easy</strong>&nbsp;<br>83</td>
<td align="center">&nbsp;<strong>ℹ️ Info</strong>&nbsp;<br>14</td>
</tr>
</table>

</div>

<div align="center"><strong>Recent badges</strong></div>

<div align="center">

<table>
<tr>
<td align="center" width="130">
<a href="https://tryhackme.com/p/ouroboroswhite">
<img src="https://assets.tryhackme.com/img/badges/careerready.png" alt="Cyber Ready" width="90"><br>
<strong>Cyber Ready</strong>
</a>
<br><sub>2026-08-17 · rare (3.4%)</sub>
</td>
<td align="center" width="130">
<a href="https://tryhackme.com/p/ouroboroswhite">
<img src="https://assets.tryhackme.com/img/badges/streak30.png" alt="30 Day Streak" width="90"><br>
<strong>30 Day Streak</strong>
</a>
<br><sub>2026-08-15 · rare (6.3%)</sub>
</td>
<td align="center" width="130">
<a href="https://tryhackme.com/p/ouroboroswhite">
<img src="https://assets.tryhackme.com/img/badges/swordapprentice.png" alt="Sword Apprentice" width="90"><br>
<strong>Sword Apprentice</strong>
</a>
<br><sub>2026-08-12 · rare (2.7%)</sub>
</td>
<td align="center" width="130">
<a href="https://tryhackme.com/p/ouroboroswhite">
<img src="https://assets.tryhackme.com/img/badges/league-platinum.png" alt="Platinum League" width="90"><br>
<strong>Platinum League</strong>
</a>
<br><sub>2026-08-10 · epic (0.3%)</sub>
</td>
<td align="center" width="130">
<a href="https://tryhackme.com/p/ouroboroswhite">
<img src="https://assets.tryhackme.com/img/badges/blue.png" alt="Blue" width="90"><br>
<strong>Blue</strong>
</a>
<br><sub>2026-08-03 · rare (8.4%)</sub>
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

For the repeatable approach behind the assessments below, from first reading the
brief through recon, exploitation, and reporting, see
[METHODOLOGY.md](METHODOLOGY.md).

## Write-ups

Short accounts of challenge rooms I solved myself, focused on the reasoning and
the security lesson rather than the step-by-step commands. See
[writeups/](writeups/).

## Security Assessment Reports

Full-format security assessment reports written to professional structure
(executive summary, scope, methodology, CVSS-rated findings with purple-team
detection analysis, and a remediation roadmap). Each one documents an assessment
I carried out myself against an authorised lab target, and is labelled as
lab-based throughout.

**All nine assessments at a glance**, ordered strongest first. Start at the top;
each row links to the full report.

| Assessment | Technique | Impact |
|---|---|---|
| [LLM Agent Security](reports/llm-agent-prompt-injection-2026-08.md) | Prompt injection, confused-deputy tool abuse | Host command execution |
| [Web & Cloud Assessment](reports/lab-assessment-2026-08.md) | CVE exploitation, cloud IAM abuse, exposed `.git` | Multi-target compromise, data-plane breach |
| [Lost-Device Forensics](reports/device-loss-data-at-rest-2026-08.md) | DPAPI, LSA secrets, registry, data-at-rest recovery | Credential recovery from an encrypted device |
| [Network Share to Root](reports/smb-to-multiuser-compromise-2026-08.md) | SMB enumeration, weak SSH credentials, key theft, sudo | Full root compromise |
| [Command-Injection Chain](reports/command-injection-chain-2026-08.md) | Command injection at two privilege boundaries | Unauthenticated edge RCE, then root |
| [Azure Cloud Attack Chain](reports/cloud-attack-chain-azure-2026-08.md) | Leaked SAS token, stolen service principal, Key Vault | Cloud secret compromise |
| [Business-Logic & API Abuse](reports/business-logic-assessment-2026-08.md) | Race condition in reward-eligibility logic | Repeated reward grant (financial abuse) |
| [Single-Host Full Compromise](reports/host-compromise-2026-08.md) | NoSQL auth bypass, SSTI, RCE, privilege escalation | Anonymous to root |
| [Recoverable XOR Cryptosystem](reports/xor-cryptosystem-2026-08.md) | Known-plaintext key recovery against repeating-key XOR | Full secret disclosure |

**Why the top three stand out**, chosen on the strength of the analysis rather
than the difficulty of the target:

1. [LLM Agent Prompt Injection](reports/llm-agent-prompt-injection-2026-08.md): an
   AI concierge agent whose model-adjudicated tool authorization was bypassed by
   routing a privileged command through an authorized record, so it inherited an
   authorization the attacker never held, reaching host command execution. The
   confused-deputy analysis in F-02 is the sharpest reasoning in this repository.
2. [Web & Cloud Assessment](reports/lab-assessment-2026-08.md): three targets,
   independently assessed. Contains a real CVE with honest notes on adapting an
   unreliable public exploit, and the detection analysis I am most confident in:
   why CloudTrail's management-plane default logging records the credential theft
   but not the data-plane read that actually causes the breach.
3. [Lost-Device Data-at-Rest Recovery](reports/device-loss-data-at-rest-2026-08.md):
   forensic recovery from a recovered laptop. A strongly encrypted container
   opened without cracking anything, because the key was stored inside the device
   it protected. Four findings that all score identically, and an appendix
   explaining why that is the honest result rather than a copied score.

These reports were written over a concentrated period of full-time study, which
the commit history reflects.

## Detection Rules

Sigma detection rules written from the attacker behaviour I produced during my
own assessments, so each offensive finding has a corresponding defensive
artefact a SOC could load. See [detections/](detections/).

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
- **Nothing is published without passing a safety gate.** A pre-commit,
  pattern-based check blocks common credential, token, private-key, CTF-flag,
  email, and local-path *shapes*. It deliberately matches credential-shaped
  *field names* and secret-shaped *values* rather than keywords, because lab
  titles legitimately contain words like "password" and "authentication"; a
  check that fires on every run is a check people learn to ignore. It is a last
  line of defence rather than comprehensive secret detection: it catches known
  patterns, not every possible encoding. It was tested against deliberately
  poisoned data, which is how a gap in it was found and closed.
- **Only an explicit allow-list of files is ever staged**, so a stray file
  in the working directory cannot be swept into a public commit.

Documented in [SETUP.md](SETUP.md).

_Built with AI assistance (Claude Code). The design decisions, priorities,
and review were mine._

## Contact

- TryHackMe: [ouroboroswhite](https://tryhackme.com/p/ouroboroswhite)
- GitHub: [ouroboros-white](https://github.com/ouroboros-white)
