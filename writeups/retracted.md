# Retracted

**Platform:** TryHackMe (Endpoint Security Monitoring) · **Difficulty:** Easy · **Date:** 2026-08-06
**Tags:** Blue Team, DFIR, Sysmon, Event Viewer, Ransomware, Incident Timeline

## The target

The capstone of the Endpoint Security Monitoring module. No exploitation: I'm handed
a Windows host (`SHIELDED-FUTURE`, user `Sophie`) and a vague user account: *"I ran
an installer for an antivirus program, and afterwards I couldn't open any of my
files."* The job is to reconstruct what actually happened from **Sysmon** logs in
Event Viewer and produce an ordered timeline. The whole room is a lesson in reading
logs against a witness statement, and the two disagree.

This was my first time working an incident from the blue-team side, reading the
evidence a host leaves behind rather than being the one who makes it.

## The one thing that made everything work

Everything downstream depended on one field: **`UtcTime`** inside each event, not the
"Date and Time" column. The column is host-local; `UtcTime` in the EventData is
unambiguous. The room's timeline question demands UTC, and the box happened to be set
to UTC anyway, but I only trusted that after confirming a `UtcTime` value matched a
displayed time on the same event. Assuming the offset instead of checking it is how
you search the wrong window and wrongly conclude an event "doesn't exist."

The navigation that mattered: *Applications and Services Logs → Microsoft → Windows →
Sysmon → Operational*, then **Filter Current Log** scoped by **Event ID** and a
custom **Logged** date range. On a ~6,000-event log the difference between filtering
and scrolling is the difference between minutes and an afternoon.

## What I tried (and three false positives I caught myself)

I went in filtering **Event ID 11 (FileCreate)** for the text file `SOPHIE.txt`,
reasoning that whatever *wrote* the file would appear in its `Image` field. That was
the right event class but it dragged me through three dead ends, each of which taught
the same lesson:

- **`__PSScriptPolicyTest_*.ps1`**: an ID 11 hit written by `powershell.exe`. It was
  *my own* elevated session: PowerShell drops a dummy script to test execution
  policy, constantly. Timestamp was *today*, not the 2024 incident. **I was
  contaminating the evidence I was reading.**
- **`DisableAntiVirus` registry write (ID 13)**: scary key name, but the value was
  `0` (AV *enabled*), the writer was `MsMpEng.exe` (Defender's own signed engine),
  and the date was almost two years off target. A key name is not a finding; the
  **value**, the **writer**, and the **date** are.
- **Sysmon ID 255 error**: *"Failed to open service configuration… the media is
  write protected."* Real, but downstream (14:27, after everything) and just as
  plausibly a lab-snapshot artifact. Logged it as an open question rather than
  building a theory on it.

The pattern behind all three: I kept clicking whatever looked *unusual* in an
unfiltered list, and unusual-looking debris clusters at the **end** of an incident,
not the start. The fix was a three-question reflex before any event earns attention.
**Is it in my window? What does the value actually say? Who wrote it, and from
where?**

## What worked: pivoting on process ancestry

The break came from switching away from ID 11 to **Event ID 1 (ProcessCreate)** and
building the timeline from `Image`, `CommandLine`, and the decisive field,
**`ParentImage`**. Two downloads sat in `C:\Users\Sophie\download\`: `antivirus.exe`
and `decryptor.exe`. `decryptor.exe` executed at **14:24:18.804**, three seconds
before a burst of thousands of file-writes. Its parent was `explorer.exe` under
Sophie's account: an interactive double-click.

I initially misread the `User` field. The lower General-tab block showed
`NT AUTHORITY\SYSTEM` and I called it privilege escalation; the **EventData** showed
the real context, `SHIELDED-FUTURE\Sophie` at **Medium** integrity. Correcting it was
the better lesson: **ransomware needs no admin**, because every file the user can open, she
can overwrite. And **`ParentImage` tells you *how* something launched, not *who*
launched it**: with an RDP logon in play, that "Sophie" session was the intruder's
hands on her account.

The `decryptor.exe` SHA-256 scored **6/75** on VirusTotal (hash lookup only, never
upload the sample). The six were the ML/behavioural engines (CrowdStrike, Elastic,
DeepInstinct, Fortinet); every signature vendor called it clean. A bespoke sample
evades **bytes**; it can't evade **behaviour**, which is exactly the trail I'd just
walked.

## The timeline (UTC, 8 Jan 2024)

| Time | Event | Evidence |
|---|---|---|
| ~14:14 | `antivirus.exe` (the malware) present/modified | Downloads metadata |
| 14:15:02 | Outbound HTTP → `10.10.8.111:80` (cleartext) | Sysmon ID 3 |
| 14:19:22 | **Inbound RDP** from `10.11.27.46` | Sysmon ID 3 / Security 4624 type 10 |
| *(pre-RDP)* | Malware **encrypts** files, drops ransom note | file-write burst |
| 14:24:18 | `decryptor.exe` run, parent `explorer.exe`, Sophie/Medium | Sysmon ID 1 |
| 14:24:21 | Mass file-write burst = **decryption** | Sysmon ID 11 |
| 14:25:16 | `SOPHIE.txt` (19 bytes) created on Desktop | Sysmon ID 11 |

The sequence the room confirms: Sophie downloads and runs the malware → it encrypts
and shows a ransom note → she leaves to call for help → the intruder logs in over RDP
→ "realises" it's a charity, downloads a decryptor and restores the files → leaves the
19-byte Desktop note telling her to check her Bitcoin → responders arrive, intruder
gone.

## Where my first narrative was wrong

Worth recording, because self-correction is the skill:

- **Two identical bursts, opposite meanings.** Encrypting and decrypting a disk
  produce the *same* Sysmon signature, thousands of writes in seconds. I only found
  the **14:24 decryption** burst and never filtered before 14:14, so I initially put
  encryption *after* the RDP login. The log cannot tell the two verbs apart; only
  context can. There was an earlier encryption burst I hadn't looked for.
- **`SOPHIE.txt` is 19 bytes**, too small for a ransom note (which must explain,
  price, and give contact). It's the *post-restore* Bitcoin note, which is why its
  timestamp lands after the decryption, not before.
- **"The hacker cleaned up, that's why there's no evidence"** was unfalsifiable and
  false: 6,100 Sysmon events survived, including the attacker's own executions. A
  real wipe leaves **Security ID 1102** ("audit log cleared"); its absence kills the
  theory. I dropped it rather than carrying it.
- **Motive is a claim, not evidence.** The charity/apology/Bitcoin story comes from a
  note *the attacker wrote*. The logs support "someone claiming remorse left a note
  and files became accessible again", not "they felt bad."

## Finding & fix

**Finding:** initial access was a socially-engineered download, malware named
`antivirus.exe` to match what the victim was searching for, executed by the user at
Medium integrity, followed by hands-on-keyboard **RDP** access from an external host
over the same window. No privilege escalation was needed to encrypt user data.

**Fix (defender):**
- **Restrict RDP**: deny internet-facing RDP, require VPN + MFA, and alert on
  `4624` **LogonType 10** from unexpected sources. The `10.11.27.46` logon is the
  event that should have paged someone.
- **Block execution from user-writable paths** (Downloads, AppData, Temp) via
  AppLocker/WDAC. `decryptor.exe` ran straight out of `C:\Users\Sophie\download\`.
- **Don't trust the AV verdict**: a sample 69/75 vendors cleared was caught by
  behaviour (parent `explorer.exe` → immediate mass file-writes). EDR and behavioural
  detection are the control, not signature AV alone.
- **Tune Sysmon coverage**: absence of a FileCreate event means the *config* wasn't
  watching that path, not that nothing happened. Know your gaps.

**The offensive read (why this matters for where I'm headed):** a custom 64-bit
binary walked past nearly every signature engine and was still trivially caught by
process ancestry and a burst of file writes. Bytes evade; behaviour betrays. Every
action on a Windows host leaves a Sysmon event: process create (1) with full command
line, network connect (3), file create (11), registry set (13). Reading the incident
from the blue side is the clearest possible map of which of *my own* future actions
are loud, and why.
