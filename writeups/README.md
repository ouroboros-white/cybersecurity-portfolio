# Write-ups

Short, structured accounts of challenges I solved myself. The point of this
folder is to show *reasoning*, which a completion count cannot: what I was
faced with, what I tried, what failed, what worked, and the underlying security
lesson.

The file names are the room names, so they say nothing about what is inside.
The index below is generated from each write-up's own header, so it stays
accurate.

For full assessment reports written to commercial deliverable standard, see
[reports/](../reports). For the complete training record, see
[TRAINING.md](../TRAINING.md).

## Index

<!--INDEX:START-->
**23 write-ups across 6 disciplines.** Each one is a challenge solved without a walkthrough. Hardest first.

### AI and LLM Security

| Write-up | Focus | Difficulty | Date |
| --- | --- | --- | --- |
| [The Guestbook](the-guestbook.md) | Web, AI, Prompt Injection, LLM01, Confused Deputy, Tool Abuse | Medium | 2026-08-08 |
| [The Concierge Knows Too Much](the-concierge-knows-too-much.md) | AI, Prompt Injection, Social Engineering, LLM Security | Easy | 2026-07-28 |

### Cloud

| Write-up | Focus | Difficulty | Date |
| --- | --- | --- | --- |
| [CryptoCabana](cryptocabana.md) | Cloud, Azure, Storage, Key Vault, SAS | Medium | 2026-08-04 |
| [Complimentary](complimentary.md) | Cloud, AWS, Cognito, DynamoDB, Broken Access Control | Easy | 2026-07-30 |

### OSINT

| Write-up | Focus | Difficulty | Date |
| --- | --- | --- | --- |
| [OhSINT](ohsint.md) | OSINT, BSSID Geolocation, Metadata, Username Pivoting, Reverse Image Search | Easy | 2026-08-23 |
| [Searchlight IMINT](searchlight-imint.md) | OSINT, IMINT, Geolocation, Reverse Image Search | Easy | 2026-08-08 |
| [Sakura](sakura.md) | OSINT, Metadata, Git Forensics, Blockchain Analysis, IMINT | Easy | 2026-08-07 |
| [Overheard at Breakfast](overheard-at-breakfast.md) | OSINT, Social Media, Hashing, Gravatar | Easy | 2026-08-02 |
| [The Brochure](the-brochure.md) | OSINT, Encoding | Easy | 2026-07-28 |

### Digital Forensics and Blue Team

| Write-up | Focus | Difficulty | Date |
| --- | --- | --- | --- |
| [Management Wants a Word](management-wants-a-word.md) | Forensics, Windows, DPAPI, Chrome Credentials, VeraCrypt | Hard | 2026-08-10 |
| [After Hours](after-hours.md) | Windows, Forensics, WMI, Persistence, Fileless, .NET, Reverse Engineering | Medium | 2026-08-08 |
| [Retracted](retracted.md) | Blue Team, DFIR, Sysmon, Event Viewer, Ransomware, Incident Timeline | Easy | 2026-08-06 |
| [Packed Light](packed-light.md) | Network Forensics, PCAP Analysis, Cryptography | Easy | 2026-07-30 |

### Cryptography

| Write-up | Focus | Difficulty | Date |
| --- | --- | --- | --- |
| [Wise Guy](wise-guy.md) | Cryptography, XOR, Known-Plaintext, Python | Easy | 2026-08-21 |

### Web Application

| Write-up | Focus | Difficulty | Date |
| --- | --- | --- | --- |
| [Infinity Pool](infinity-pool.md) | Web, Command Injection, Reverse Shell, Pivoting, Port Forwarding, FreePBX, Privilege Escalation | Medium | 2026-08-06 |
| [The Hollow Shell](the-hollow-shell.md) | Web, File Upload, Zip Slip, Path Traversal, Flask Sessions, RCE, Reverse Shell | Medium | 2026-08-06 |
| [Towel on the Sunbed](towel-on-the-sunbed.md) | Web, Business Logic, Race Condition, API Abuse | Medium | 2026-08-03 |
| [Do Not Disturb](do-not-disturb.md) | Web, Boot2Root, NoSQL Injection, SSTI, Node.js, Privilege Escalation | Medium | 2026-08-02 |
| [Simple CTF](simple-ctf.md) | Web, SQL Injection, CVE, Hash Cracking, Privilege Escalation, GTFOBins | Easy | 2026-08-23 |
| [Beach Bar](beach-bar.md) | Web, Insecure Deserialization, Reverse Shell, Privilege Escalation, Credential Reuse | Easy | 2026-08-01 |
| [Vulnerability Capstone](vulnerability-capstone.md) | Web, Vulnerability Research, CVE, Public Exploit, RCE | Easy | 2026-08-01 |
| [Neighbour](neighbour.md) | Web, Information Disclosure, Broken Access Control | Easy | 2026-07-28 |
| [Room 404](room-404.md) | Web, Source Disclosure, Recon | Easy | 2026-07-28 |
<!--INDEX:END-->

## The bar

- **Only rooms I actually worked out.** Guided walkthrough rooms belong in
  [TRAINING.md](../TRAINING.md) as completions, not here. If the room handed me
  the answer, there is nothing to write up.
- **Reasoning, not a command log.** The failed attempts and the "why" matter
  more than the exact commands.
- **Tight.** Four sections (below), no padding. One focused page beats three
  rambling ones. Length follows the investigation: a quick room stays short, a
  layered one earns more room.
- **No flags.** Never paste a room's flag or answer.

## The shape

Every write-up follows [TEMPLATE.md](TEMPLATE.md):

1. **The target** - what I was up against, in a sentence or two.
2. **What I tried** - including the dead ends.
3. **What worked** - the step that cracked it, and why it worked.
4. **Finding & fix** - the real vulnerability in a line, and how I would defend
   against it.

Repo conventions and the publishing checklist live in
[CONTRIBUTING.md](../CONTRIBUTING.md).
