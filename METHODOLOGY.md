# Assessment Methodology

My repeatable approach to a target, from first reading the brief through to a
finished report. It is aligned to the Penetration Testing Execution Standard
(PTES), with the OWASP Web Security Testing Guide (WSTG) for the web tier and the
OWASP Top 10 for LLM Applications for AI targets.

The value of a fixed method is that the early steps become automatic, so my
attention goes to the part of each target that is actually different. The steps
below are the spine. The **branches** at the end adapt it to web-only, cloud,
forensic, and LLM-agent targets.

Every report in [reports/](reports/) follows this. Where a report compresses it
to a phase list, this document is the long form behind it.

---

## The core loop: discover, then interrogate

Every phase below, at every tier, runs the same two beats, and naming them is
what stops recon becoming a directionless tool-dump:

1. **Discover.** Enumerate a surface for what it exposes: ports on a host, paths
   on a web app, shares on SMB, records in DNS.
2. **Interrogate.** Open and read *every single thing* discovery returned. The
   tool provides the doors; each one still has to be walked through. This is the
   half skipped most often and where the finding usually is.

More tools and bigger wordlists is the beginner trap: it widens *discover* while
starving *interrogate*. Depth on what you have already found beats breadth of
what you scanned.

---

## Step 0: Read the brief and fix the scope

Before touching the target:

- Read the brief in full. Note the stated goal, the starting position
  (unauthenticated, credentialed, black or white box), and any hint about the
  target's nature.
- Establish **scope and rules of engagement** as a hard gate. Before a single
  packet, confirm each of these, because a technically correct test outside them
  is an unauthorised one under the Computer Misuse Act:
  - **In-scope** hosts, IP ranges, domains, and accounts, and what is explicitly out.
  - **Allowed techniques**, and any that are prohibited.
  - **Rate limits**, and whether any denial-of-service or load testing is barred.
  - Whether **credential attacks** (brute force, spraying) are permitted.
  - Whether **exploitation and privilege escalation** are permitted, or proof-of-vulnerability only.
  - **Data-handling and evidence** rules: what may be accessed, stored, or exfiltrated.
  - **Stop conditions**: findings or events that require pausing and reporting at once.
- Note the **answer format or objective** where the brief gives one. It often
  tells you what class of finding to expect and how far the intended path goes.
- Decide what "done" looks like for this target, so I stop at proof rather than
  over-testing.

Nothing is scanned until this is settled.

---

## Passive reconnaissance (before you touch the target)

On a real external engagement or a bug-bounty scope you are handed a name, not a
single IP, and the largest wins come from surface nobody else is testing. This
tier gathers intelligence **without sending a packet to the target**, so it
carries no risk and needs no active-testing authorisation.

- **Subdomain enumeration** (`subfinder`, `amass` passive, `assetfinder`). Each
  subdomain is a separate application with its own bugs; a forgotten `staging.`
  or `dev.` host is a classic way in.
- **Certificate transparency** (`crt.sh`). Every TLS certificate an organisation
  issues is logged publicly, so this leaks internal and staging hostnames for
  free.
- **Historical URLs** (`waybackurls`, `gau`). The Wayback Machine and common
  crawl remember endpoints, parameters, and files removed from the live site that
  often still work.
- **Search dorking** (`site:`, `inurl:admin`, `filetype:`) to surface documents
  and panels the site never linked.
- **Public code and leaks.** Search GitHub for the org name, hardcoded keys, and
  internal URLs.

**On a single-IP lab box (most TryHackMe rooms) this tier is nearly empty** - no
domain, no certificate history, no public code - which is why the active scan
below comes almost first. Note the tier so the habit exists when a real scope
arrives; do not invent it where it does not apply.

---

## Step 1: Confirm the target is alive

```bash
ping -c 3 <ip>
```

A routing and reachability sanity check. A non-reply is not conclusive: many
hosts drop ICMP, so a silent target still gets scanned.

---

## Step 2: Full port, service, and version scan

The single most important step. Every branch below is chosen from what this
returns.

**Fast pass first, so I can start working while the full scan runs:**
```bash
nmap -T4 --top-ports 1000 <ip>
```

**Full TCP scan (let this run in the background):**
```bash
nmap -sC -sV -p- <ip>
```

- `-p-` covers all 65535 ports, so a service on a high port is not missed.
- `-sV` fingerprints service versions. A version number here is frequently the
  whole target.
- `-sC` runs the default script set for quick, safe enumeration.

**UDP is not optional.** TCP scans miss services that only listen on UDP:
```bash
nmap -sU --top-ports 20 <ip>
```
SNMP (161), DNS (53), TFTP and IKE live here, and open SNMP in particular can
disclose a large amount of the host.

**Do not wait on the full scan.** `-p-` takes minutes; the fast top-1000 pass,
and browsing any web service the scan has already revealed, run in parallel with
it. Browsing as a user is the least intrusive active step there is and has no
dependency on the full scan finishing.

Record **every** open port and its version, not only the obvious web ports. If
version detection is thin, follow up with targeted scripts
(`nmap -p <port> --script <category>`), or grab the banner manually
(`nc <ip> <port>` / `telnet`) for a service nmap fingerprints poorly.

---

## Step 3: Branch on the services found

Recon is not linear from here. The open ports decide the route, and this is where
judgement replaces routine:

| Service | First move |
|---|---|
| **80 / 443 / 8080 (web)** | Go to Step 4. Usually the primary surface. |
| **22 (SSH)** | Note it. Normally the way *in* once credentials or a key exist, not the first attack. |
| **21 (FTP)** | Test for anonymous login; check for readable or writable files. |
| **139 / 445 (SMB)** | Enumerate shares and users (`enum4linux-ng`, `smbclient`). Anonymous shares often leak valid usernames. |
| **53 (DNS)** | Attempt a zone transfer (`dig axfr @<ip> <domain>`); it can hand over every record at once. |
| **161/UDP (SNMP)** | `snmpwalk` with common community strings. Frequently dumps processes, users, and network detail. |
| **3306 / 5432 / 1433 (DB)** | Note version; test for default or weak credentials. |
| **25 / 110 / 143 (mail)** | Note version; consider user enumeration. |
| **Anything unusual** | Record the version and research it (Step 5) before moving on. |

**Before enumerating a web service, resolve the hostname.** Many targets route by
`Host:` header or only render correctly by name. Add the host to `/etc/hosts`,
then look for virtual hosts and subdomains that are otherwise invisible:
```bash
ffuf -H "Host: FUZZ.<domain>" -u http://<ip> -w <wordlist>
```
Skipping this is the most common reason a target looks empty when it is not.

---

## Step 4: Web enumeration

When a web service is present, the surface is mapped before anything is attacked.

**Run everything through an intercepting proxy (Burp Suite, or OWASP ZAP).** A
proxy sits between your browser and the target and records every request and
response, then lets you pause, edit, and replay any of them. It is the spine of
web testing: it is how you see the real request behind a button click, tamper
with a value the interface will not let you change, and resend a request as a
different user. Browser dev tools and `curl` cover the light cases; the proxy is
what you work inside.


1. **Browse it like a user first.** Understand what the application is for. The
   intended function is where business-logic flaws live.
2. **View source on every page.** Comments, hidden fields, and linked JavaScript
   frequently disclose endpoints, credentials, or logic.
3. **Content discovery.** Brute-force paths and files:
   ```bash
   gobuster dir -u http://<ip> -w <wordlist>
   ```
   `ffuf` or `feroxbuster` do the same job; the tool is a preference, the step is
   not. Vary the wordlist and extensions to the stack.
4. **Check `robots.txt`, `sitemap.xml`, and any path they reveal.**
5. **Check for exposed version control and backups.** Request `/.git/`, `/.svn/`,
   and common backup or saved-config names (`.bak`, `~`, `.old`,
   `config.php.save`). An exposed `.git` can be reconstructed with `git-dumper`,
   history and secrets included.
6. **Open every path content discovery finds and read it.** The tool provides
   the doors; each one still has to be opened and understood. This is the step
   most often skipped and most often where the finding is.
7. **Fingerprint the stack.** Response headers, error pages, framework tells,
   login endpoints, and any exposed version. On HTTPS, read the TLS certificate,
   which often leaks hostnames, internal names, and emails. Feed anything
   versioned into Step 5.
8. **Test authentication and the account lifecycle**, not just the login. Weak
   and default credentials are one part. Also examine registration, password
   reset, MFA, account recovery, session invalidation on logout, session
   fixation, account enumeration (does a wrong username differ from a wrong
   password), and lockout or rate limiting. Then the injection classes the login
   invites (SQL, NoSQL), and fuzz for hidden parameters (`ffuf`, `arjun`).
9. **Map the API from its own client-side script** where the app is JS-driven,
   so the real endpoints and parameters are known before testing.
10. **Test authorization, in every direction.** This is the highest-yield web
    bug class and the one scanners miss, because it needs a human who understands
    who is allowed to do what. Changing `id=1` to `id=2` is one instance, not the
    whole class. Test:
    - **Horizontal**: user A reaching user B's data (classic IDOR).
    - **Vertical**: an ordinary user performing a privileged action.
    - **Object-level**: any reference to a record, including non-numeric ones
      (UUIDs, slugs, filenames) and references leaked in responses.
    - **Function-level**: an admin-only endpoint or path requested directly as a
      low user or anonymous.
    - **API-level**: the same checks against the API, where the UI hid the control
      but the server never enforced it.
    Keep an authorization matrix: for each role, which endpoints *should* work,
    and test every cell that should not. Authorization enforced in the UI but not
    server-side is the recurring finding.
11. **Test every input against the injection classes, systematically.** For each
    parameter, header, and body field, ask which interpreter it might reach and
    probe accordingly: **SQL / NoSQL** (database), **command injection** (shell),
    **SSTI** (template engine), **path traversal / LFI** (filesystem), **XSS**
    (other users' browsers), **SSRF** (server-side requests), **XXE** (XML
    parsers). One unsanitised input reaching any of these is usually the whole
    finding. The WSTG input-validation section is the full checklist.
12. **Sweep the configuration and the edges.** Security headers and their absence,
    cookie attributes and token handling, CORS policy, CSRF protection on
    state-changing requests, file upload and download handling, error pages and
    stack traces (information disclosure), rate limiting and abuse controls, and
    any GraphQL or WebSocket surface. Then the **business-logic invariants**: the
    rules the application assumes but never enforces.

---

## Step 5: Vulnerability analysis

Turn what recon found into candidate weaknesses.

**Model the trust boundaries first.** Before firing vulnerability categories at
inputs, map where untrusted data crosses into trusted execution: which inputs an
attacker controls, where each one flows, and which component finally acts on it.
Weakness categories are then aimed at those boundaries, not sprayed at everything.
OWASP-style lists are a coverage reference, not a script to run blindly.

```bash
searchsploit <service> <version>
```

- Match services and versions against known vulnerabilities (CVE / Exploit-DB).
- **A version string is a candidate, not a confirmed vulnerability.** Confirm the
  exact product, version or build, configuration, and affected component, then
  establish applicability to this target before claiming it. Prefer the vendor
  advisory or primary source over an exploit title, and validate with the safest
  check that proves it.
- Map application behaviour to weakness classes (CWE) and to logic or
  configuration flaws that no scanner names.
- Prioritise by likely impact before spending effort on exploitation.

---

## Step 6: Exploitation

- Prove impact with the **least intrusive action** that demonstrates the finding.
  Proof, not destruction.
- Capture the request, the response, and the result as evidence at the moment it
  works (see Evidence, below).
- Where a public exploit is used, understand it before running it.

---

## Step 7: Post-exploitation and privilege escalation

- Stabilise the foothold (upgrade to a proper TTY where relevant).
- Enumerate for escalation: users and groups, `sudo` rights, SUID binaries,
  readable credentials and keys, scheduled tasks, service accounts, internal-only
  services. Automated enumeration (for example `linpeas`) supplements manual
  checks, it does not replace them.
- Identify and follow the path to root or Administrator.
- Look for lateral movement: reused credentials, keys, and trust relationships to
  other accounts or hosts.

---

## Evidence: capture as you go

Throughout every step, evidence is recorded live rather than reconstructed from
memory afterwards. Command in, output out, at the time it happened. A finding is
only as trustworthy as the evidence captured when it was proven, and a report is
never rated on unverified recall.

---

## Step 8: Reporting handoff

Recon and exploitation feed a report that follows the same structure every time:

- Executive summary and findings-at-a-glance table.
- Scope and rules of engagement.
- This methodology (referenced or summarised).
- Attack (or recovery) path, with **MITRE ATT&CK** technique mapping (ATLAS for
  AI targets).
- Detailed findings: each with **CVSS v3.1** base score, **CWE** identifier,
  evidence, and a **detection analysis** framed as expected detection
  opportunities, since lab targets are not instrumented.
- Remediation roadmap, prioritised.
- Retesting procedure, stating how each fix would be verified.

---

## Branches: adapting the spine to the target

The core above is a host methodology. These are the documented deviations, one
per target type in the portfolio.

### Web-application-only target

No host to escalate on. Steps 1 to 3 shrink to confirming the single web service;
the work is Step 4 in depth, then business-logic testing (WSTG-BUSL): map the
API from its client-side script, model the mechanism, and test state-changing
endpoints for logic and concurrency flaws (for example race conditions on a
value-granting endpoint). Tooling is often just browser developer tools and
`curl`.

### Cloud target

Recon is identity-first, not port-first: enumerate the granted identity, pivot to
what the application itself trusts, follow each credential to the next resource,
and recover the objective. Tooling is the provider CLI (`az`, `aws`). Watch the
split between management-plane and data-plane logging, because it changes what a
defender can see and drives the detection analysis.

### Forensic / data-at-rest target

Not a live attack. Preservation comes first: **hash the original on
acquisition, record the acquisition metadata, and never modify the evidence.**
All work happens on a verified **copy**, with containers mounted **read-only**.
Only then inventory the artifacts, identify the sensitive target and the controls
protecting it, and reconstruct the offline recovery path from lowest-privilege
data upward. Tooling such as `impacket` (`secretsdump`, `dpapi`) and `cryptsetup`.

### LLM-agent target

Aligned to the OWASP Top 10 for LLM Applications. Recon is trust-boundary
mapping: the model, its system and developer instructions, its tools, each
tool's permissions, its data sources, its memory or state, its users, and its
external side effects. The core question is then whether **attacker-controlled
input can cross one of those boundaries** and drive the agent to take an action
the attacker is not authorised to take. Prompt injection is one mechanism for
that crossing, not the whole test. A hard-won note: read and, where needed,
**reset to a clean baseline** before interacting, because polluted state makes
cause and effect unreadable and the enabling behaviour is often only visible
against the default state.
