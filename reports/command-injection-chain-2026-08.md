# Security Assessment Report: Command-Injection Chain to Root

**Assessment type:** Black-box web-to-root compromise of a single host
**Environment:** TryHackMe training target ("Infinity Pool", Hacker Holidays)
**Assessor:** ouroboros-white
**Report date:** 2026-08-06
**Version:** 1.0
**Classification:** Public

---

> **About this document.** This is a real assessment against a **lab target**,
> written to professional structure. All reconnaissance, exploitation, and
> evidence collection described here was carried out by me against that target.
> Nothing in it is hypothetical, and none of it is reproduced from a walkthrough.
> It is not a live client engagement, and no production system or third party was
> tested. It documents a full web-application-to-root
> compromise of a single host to demonstrate the reporting deliverable: an attack
> path, CVSS-rated findings, detection analysis, and remediation. Target
> identifiers and secrets are redacted as they would be in a client report; no
> flags are reproduced.

---

## 1. Executive summary

A single host running a Python/Flask web application was compromised from an
unauthenticated starting point through to full **root** control. The striking
feature of this target is that the first and last links in the chain are the
**same vulnerability**, user input concatenated into an operating-system shell
command, appearing first at the public edge (as a low-privilege service account)
and again in a privileged internal worker (as root). The intervening steps did
not require exploitation so much as **reading what the environment volunteered**:
an internal console with no authentication that disclosed credentials, and a
privileged API key distributed as a voicemail.

An attacker with no credentials could: run arbitrary commands on the server as
the web account, enumerate internal-only services, recover a set of application
credentials, retrieve a root API token from a voicemail box, and finally run
arbitrary commands **as root** through that API. The most serious issues are the
two command-injection flaws (F-01, F-04); the connective tissue is a missing
internal authentication boundary (F-02) and weak secret handling (F-03).

While each finding is rated individually below, **the combined real-world
severity is Critical**: the chain results in complete compromise of the host.

### Findings at a glance

| ID | Finding | Severity | CVSS 3.1 |
|----|---------|----------|:--------:|
| F-01 | Unauthenticated OS command injection in the connectivity-check feature | **Critical** | 9.8 |
| F-02 | Internal service trusts network position; discloses credentials | **Medium** | 6.5 |
| F-03 | Default credentials and a privileged API token exposed via message store | **Medium** | 6.5 |
| F-04 | OS command injection in the root-privileged automation worker | **High** | 7.8 |

**Attack chain at a glance** (severity-highlighted for a management audience):

```mermaid
flowchart TD
    S["Unauthenticated attacker"] --> F1["F-01 Edge command injection · CRITICAL"]
    F1 --> F2["F-02 Unauthenticated internal console · MEDIUM"]
    F2 --> F3["F-03 Default credentials and Bearer token exposure · MEDIUM"]
    F3 --> F4["F-04 Root automation worker command injection · HIGH"]
    F4 --> R["Full root compromise"]
    classDef crit fill:#b91c1c,stroke:#7f1d1d,color:#ffffff;
    classDef high fill:#c2410c,stroke:#7c2d12,color:#ffffff;
    classDef med fill:#a16207,stroke:#713f12,color:#ffffff;
    classDef term fill:#1f2937,stroke:#111827,color:#ffffff;
    class F1 crit;
    class F4 high;
    class F2,F3 med;
    class S,R term;
```

Each finding also carries a **detection analysis**: the telemetry a monitored
environment would generate and why the activity would or would not be caught. As
with lab targets generally, these are expected detection opportunities rather
than observed fact, because the host carries no instrumentation of its own.

---

## 2. Scope and rules of engagement

| Item | Detail |
|------|--------|
| **In-scope asset** | A single host exposing SSH (22) and a Python/Flask web application (80), plus its internal (loopback-only) services. |
| **Perspective** | External, black-box, unauthenticated. No credentials or prior knowledge supplied. |
| **Objective** | Achieve and demonstrate the highest level of access obtainable (root). |
| **Excluded** | Denial-of-service, destructive actions, and any target outside the named host. |
| **Authorisation** | Performed within the TryHackMe platform terms, which authorise exploitation of the provided target. |
| **Window** | 2026-08-06. |

### Target asset

| Attribute | Detail |
|-----------|--------|
| **Hostname** | `tryhackme-24xx` (internal hostname; redacted as it would be in a client report) |
| **IP address** | Redacted. Single in-scope host on the lab network. |
| **Operating system** | Ubuntu Linux (server; confirmed via the `OpenSSH … Ubuntu` service banner) |
| **Externally exposed services** | 22/tcp SSH (OpenSSH 9.6p1); 80/tcp HTTP (gunicorn / Flask) |
| **Internal (loopback-only) services** | 3000/tcp ops console; 8080/tcp FreePBX 16.0.45; 9000/tcp automation worker (runs as root) |
| **Assessment date** | 2026-08-06 |

---

## 3. Methodology

The assessment followed a standard offensive workflow aligned to the Penetration
Testing Execution Standard (PTES) and, for the web layer, the OWASP Web Security
Testing Guide (WSTG): reconnaissance, enumeration, vulnerability analysis,
exploitation, post-exploitation and privilege escalation, then reporting.
Severity is expressed as CVSS v3.1 base score, and each finding is mapped to a
Common Weakness Enumeration (CWE) identifier. Detection analysis describes
expected detection opportunities, since the target is not instrumented, and a
retesting procedure in section 7 states how each fix would be verified.

**Tooling:** `nmap`, `curl`, browser developer tools, `ss`/`systemctl`, `chisel`
(reverse port-forwarding to reach loopback services), and standard Linux
utilities. No destructive tooling was used.

---

## 4. Attack path

```mermaid
flowchart TD
    A["Public Flask app (80)"] --> B["F-01: OS command injection in /internal/netcheck"]
    B --> C["Reverse shell as 'web'; user flag"]
    C --> D["F-02: internal Watchtower console (3000), no auth, leaks config"]
    D --> E["Recovered FreePBX UCP credentials + automation endpoint"]
    E --> F["F-03: voicemail discloses root automation bearer token"]
    F --> G["F-04: OS command injection in automation worker (9000), as root"]
    G --> H["Arbitrary command execution as root; root flag"]
```

The value of this engagement is the chain, so it is documented as a path before
the findings are detailed individually.

1. **Entry (F-01).** The public "connectivity check" passed a user-supplied host
   into a shell `ping` command. A command-separator payload achieved arbitrary
   command execution as the web service account, `web`; a reverse shell recovered
   the user-level objective.
2. **Internal discovery (F-02).** From that foothold, three loopback-only
   services were visible. An internal "Watchtower" console required no
   authentication (it trusts any localhost connection) and its configuration
   endpoint disclosed application credentials and the address of a privileged
   automation service.
3. **Secret recovery (F-03).** The disclosed credentials were unrotated defaults
   for the telephony application. They granted access to a voicemail box whose
   message carried the **bearer token** for the root automation worker.
4. **Root (F-04).** The automation worker (running as root) built a shell command
   from a user-supplied `report` field. The same injection technique as F-01
   yielded arbitrary command execution as root.

A dead end is worth recording: a public FreePBX authenticated-RCE exploit
matched the version banner, but out-of-band testing proved the code path was
patched: the API returned a success acknowledgement without executing injected
commands. The genuine route was secret recovery, not that exploit.

Each rung depended on the one before it; none required insider access.

### ATT&CK technique mapping

| Stage | Finding | Tactic | Technique |
|---|---|---|---|
| Command injection in the public connectivity-check feature | F-01 | Initial Access | T1190 Exploit Public-Facing Application |
| Commands and a reverse shell run as the `web` account | F-01 | Execution | T1059.004 Command and Scripting Interpreter: Unix Shell |
| Enumerating loopback-only services from the foothold | F-02 | Discovery | T1046 Network Service Discovery |
| Configuration endpoint disclosing application credentials | F-02 | Credential Access | T1552 Unsecured Credentials |
| Unrotated default credentials accepted by the telephony application | F-03 | Initial Access | T1078.001 Valid Accounts: Default Accounts |
| Bearer token for the automation worker recovered from a stored message | F-03 | Credential Access | T1528 Steal Application Access Token |
| Command injection in the root-privileged automation worker | F-04 | Privilege Escalation | T1068 Exploitation for Privilege Escalation |
| Commands run as root through that worker | F-04 | Execution | T1059.004 Command and Scripting Interpreter: Unix Shell |

Two notes on the choices above.

**T1046 is used here in its proper post-compromise sense.** The loopback-only
services were invisible from outside and only became enumerable once F-01 provided
a shell on the host, which is exactly the situation the technique describes.

**T1528 is an imperfect fit for the bearer token.** ATT&CK frames it around cloud
and OAuth application tokens, and this was an API token for an on-host automation
service. It is used because the behaviour is the same, stealing a token that
authenticates as an application rather than a user, and no closer identifier
exists.

---

## 5. Detailed findings

### F-01: Unauthenticated OS command injection in the connectivity-check feature

| | |
|---|---|
| **Severity** | **Critical** |
| **CVSS 3.1** | 9.8, `AV:N/AC:L/PR:N/UI:N/S:U/C:H/I:H/A:H` |
| **CWE** | CWE-78: Improper Neutralization of Special Elements used in an OS Command |
| **Affected component** | Public web app, `/internal/netcheck` connectivity check |
| **Status** | Open |

**CVSS rationale.** `AV:N` and `PR:N` because the endpoint is reachable and
exploitable over the network with no authentication, and `UI:N` as no victim
interaction is required; `C:H/I:H/A:H` because arbitrary command execution
compromises the host's confidentiality, integrity, and availability outright.

**Description.** A staff "connectivity check" reachable without authentication
accepted a `host` parameter and passed it into an operating-system `ping` command
built by string interpolation and executed through a shell. Supplying shell
metacharacters allowed arbitrary commands to run on the server.

**Evidence (sanitised).** A benign value returned reflected `ping` output,
confirming server-side shell execution and an output channel. A payload of the
form `127.0.0.1; <command>` executed `<command>` as the web service account and
returned its output. The underlying code interpolated the parameter into a shell
string with shell execution enabled.

**Business impact.** Full remote code execution on the host as the web service
account, from an unauthenticated position: the gateway to the entire compromise.

**Expected detection opportunities.** High-fidelity signals: the web service
process spawning a shell or `ping` with an unexpected argument, and outbound
connections from the web account (the reverse shell). At the application edge, a
WAF can flag shell metacharacters (`;`, `|`, `` ` ``, `$(`) in the `host` field.
Not observed here, as the app performed no such logging.

**Remediation.** Do not build shell commands from user input. Invoke the command
with an argument array and no shell (e.g. `subprocess.run(["ping","-c","1",host])`),
and validate `host` against a strict IP/hostname allowlist. Require
authentication for staff tooling.

### F-02: Internal service trusts network position and discloses credentials

| | |
|---|---|
| **Severity** | **Medium** |
| **CVSS 3.1** | 6.5, `AV:L/AC:L/PR:L/UI:N/S:C/C:H/I:N/A:N` |
| **CWE** | CWE-306: Missing Authentication for Critical Function (with CWE-200: Exposure of Sensitive Information) |
| **Affected component** | Internal "Watchtower" ops console (loopback, port 3000) |
| **Status** | Open |

**CVSS rationale.** `AV:L/PR:L` because reaching the loopback console requires an
existing low-privilege foothold on the host; `S:C` (scope changed) because the
disclosed credentials authenticate to the telephony application, a component under
a different security authority from this console; `C:H` for the credential
disclosure, with `I:N/A:N` because reading the configuration endpoint neither
alters nor denies anything. The integrity and availability loss that follows from
*using* those credentials is attributed to the findings that use them, not counted
again here.

**Description.** An internal operations console bound to localhost performed no
authentication, trusting any connection that originated on the host ("authenticated
by network position"). Its configuration endpoint returned sensitive data in clear
text, including application credentials and the address of a privileged internal
service.

**Evidence (sanitised).** From the F-01 foothold, an unauthenticated request to
the console's configuration endpoint returned application credentials (self-labelled
as unrotated defaults) and the network location of the automation worker.

**Business impact.** Network-position trust provides no protection once an
attacker has any foothold on the host. The disclosure directly supplied the
credentials and target for the next stage, changing scope by exposing other
components' secrets.

**Expected detection opportunities.** Primarily preventive: an internal service
with no authentication is a configuration-review finding. Detectively, requests
to a sensitive configuration endpoint from a service account, or that account
reading credentials it never normally uses, are anomalous.

**Remediation.** Authenticate internal services with real credentials or mutual
TLS; never treat loopback or network location as identity. Remove secrets from
configuration responses and return only what a client needs.

### F-03: Default credentials and a privileged API token exposed via message store

| | |
|---|---|
| **Severity** | **Medium** |
| **CVSS 3.1** | 6.5, `AV:L/AC:L/PR:L/UI:N/S:C/C:H/I:N/A:N` |
| **CWE** | CWE-1392: Use of Default Credentials (with CWE-522: Insufficiently Protected Credentials) |
| **Affected component** | Telephony application (FreePBX) voicemail; automation bearer token |
| **Status** | Open |

**CVSS rationale.** `PR:L` because the default credentials are used from the
existing foothold; `S:C` because the recovered token authorises action on the
automation worker, a separate service under its own security authority; `C:H`
reflects exposure of a secret that authorises root-level action, with `I:N/A:N` as
the disclosure alone changes and denies nothing. The root compromise the token
makes possible is scored once, at F-04.

**Description.** The telephony application retained **default, unrotated
credentials**. Those credentials granted access to a voicemail box that stored the
**bearer token** for the root-privileged automation service in recoverable form
(as a message). A secret authorising root-level action was therefore obtainable
by anyone who could read the mailbox.

**Evidence (sanitised).** The credentials disclosed in F-02 authenticated to the
telephony user portal. A voicemail message disclosed a bearer token (redacted)
associated with the automation service on port 9000.

**Business impact.** A single reused/default login yielded the authentication
secret for a root-privileged API, collapsing the distance between a low-privilege
foothold and root (F-04).

**Expected detection opportunities.** Preventive controls dominate: enforced
rotation of default credentials, and secrets never stored in user-readable message
content. Detectively, first-ever logins to the portal from a service context, and
retrieval of the message carrying the token, are candidate signals.

**Remediation.** Rotate all default credentials on deployment and enforce this in
provisioning. Never distribute API secrets through message stores; issue them via
a secrets manager with short lifetimes and audited access.

### F-04: OS command injection in the root-privileged automation worker

| | |
|---|---|
| **Severity** | **High** |
| **CVSS 3.1** | 7.8, `AV:L/AC:L/PR:L/UI:N/S:U/C:H/I:H/A:H` |
| **CWE** | CWE-78: Improper Neutralization of Special Elements used in an OS Command |
| **Affected component** | Internal automation worker `/jobs/export` (loopback, port 9000), running as root |
| **Status** | Open |

**CVSS rationale.** `AV:L/PR:L` because the worker is loopback-only and requires
the recovered token; `S:U` because the worker already runs as root, so command
execution within it stays inside the security authority it holds and crosses no
boundary; `C:H/I:H/A:H` for full root compromise. 7.8 is the arithmetic ceiling
for an `AV:L/PR:L` finding scored `S:U`, which is why the headline severity of
this engagement is carried by the chain rather than by this score.

**Description.** The automation worker, running as **root**, constructed a shell
command (a `tar` export) by interpolating a caller-supplied `report` field into the
command string, then executed it and returned its output. Shell metacharacters in
`report` produced arbitrary command execution as root. This is the same weakness
class as F-01, one privilege tier higher.

**Evidence (sanitised).** With the bearer token from F-03, a baseline request
returned the exact shell command the worker executes, revealing the `report` value
inserted into the command. A payload terminating the `tar` and appending a command
(with the trailing template text commented out) executed as root and returned
`uid=0(root)` in the reflected output. Substituting a file-read command recovered
root-owned content.

**Business impact.** Complete root compromise of the host: unrestricted read/write
of all data, persistence, and full control.

**Expected detection opportunities.** The highest-fidelity signal is the root
automation process spawning unexpected children (a shell, `id`, `cat`) rather than
only `tar`. Kernel audit rules on `execve` by that service, and egress from the
root worker, would flag the activity. At the API edge, shell metacharacters in the
`report` field are detectable and blockable.

**Remediation.** Build the export with an argument array and no shell; strictly
validate `report` against an allowlist of known report names. Run the worker as a
dedicated unprivileged account with only the file access it needs, so a defect
cannot yield root.

---

## 6. Remediation roadmap

| Priority | Action | Findings |
|:--------:|--------|----------|
| **1 (Now)** | Eliminate shell string-building; use argument arrays and input allowlists in both the edge check and the export worker | F-01, F-04 |
| **2 (Now)** | Drop root from the automation worker; run it as a least-privilege account | F-04 |
| **3 (Now)** | Add real authentication to internal services; stop trusting network position; strip secrets from config responses | F-02 |
| **4 (Now)** | Rotate default credentials; remove API tokens from message stores | F-03 |
| **5 (Ongoing)** | Adopt a secure-command-execution standard and a secrets-management policy across all services | All |

---

## 7. Retesting

Each finding below states the specific check that confirms the fix, so a retest
produces a pass or fail rather than an opinion. A retest should begin from the same
external, unauthenticated position as the original assessment, and the chain should
be re-walked end to end afterwards: individually fixed findings can still leave a
viable path if a replacement weakness is introduced.

| Finding | Retest check | Pass condition |
|---|---|---|
| F-01 | Submit a metacharacter set (`;`, `\|`, `` ` ``, `$( )`, `&`, newline) in the `host` field, and separately confirm the endpoint now requires authentication | No payload alters the command executed; `host` is rejected unless it matches a valid IP or hostname; the endpoint is not reachable unauthenticated |
| F-02 | From a foothold on the host, request the internal service's configuration endpoint with no credentials | The service refuses unauthenticated callers, and no response field contains credential material |
| F-03 | Attempt a portal login with the previously disclosed default credentials, and replay the **originally captured** API token against the worker | Both are rejected; the default password is changed and the exposed token is revoked, not merely moved |
| F-04 | With a valid token, submit the same metacharacter set in the `report` field; separately, confirm the worker's runtime account | No payload alters the command executed; `report` is rejected unless it matches an allowlisted report name; the worker process runs as an unprivileged account, not root |

Three points decide whether this retest is meaningful.

**A payload list that fails is weak evidence for an injection fix.** The common
wrong fix here is a blocklist that strips the characters seen in the original
report. A retest built from those same characters then passes while the flaw
survives, because shell metacharacter space is larger than any blocklist: newline,
`&`, `$()`, backticks, `${IFS}`, and encoded variants all reach the shell by
different routes. The strong evidence is the implementation, so the retest should
confirm at code or configuration level that the command is invoked with an argument
array and no shell, and treat the payload run as a supporting check rather than the
finding's pass condition. Where source access is unavailable, an error message that
rejects the input by *format* ("not a valid hostname") rather than by *content*
("illegal character") is the observable tell that validation is an allowlist.

**F-04 carries two independent fixes and both need testing.** Correcting the
injection while leaving the worker as root means the next defect in that service is
root again. Dropping root while leaving the injection means arbitrary execution as
the service account, which is still a foothold and still a finding. Verify the
runtime account with a live process listing rather than from the unit file, since a
drop-in override can restore `User=root` without the original file changing.

**Rotation is part of the fix, not an extra.** F-03 disclosed a live default
password and a live bearer token. Removing the token from the message store does
nothing about the copy already captured, so the retest has to confirm the old
values fail, not that the message store is clean.

Finally, the edge fix and the worker fix should be confirmed independently. They are
the same weakness class at two privilege tiers, and a single shared patch to one
code path can leave the other untouched while appearing to resolve both.

---

## 8. Conclusion

This host was taken from anonymous to root by exploiting **one weakness twice**:
user input concatenated into a shell command, first at the public edge and again
in a root-privileged worker. Between those two ends, the environment simply handed
over what an attacker needed: an internal console that trusted anyone on
localhost and leaked credentials, a default login, and a root token left in a
voicemail. The unifying lesson is that a vulnerability **class** must be fixed
everywhere it appears, not patched at one instance while left open at another, and
that **no single trusted assumption** ("it's only on localhost," "it's only the
web account," "it's an internal API") should be enough to advance an attacker to
the next level. Every link here was individually cheap to fix.

---

## Appendix A: Severity methodology

Severity is CVSS v3.1 base score. Bands: Critical 9.0 to 10.0, High 7.0 to 8.9,
Medium 4.0 to 6.9, Low 0.1 to 3.9.

F-01 and F-04 are the same class of defect, unsanitised input reaching an OS
shell, and they are scored differently on purpose. F-01 rates 9.8 because it is
reachable by anyone on the network with no credential; F-04 rates 8.8 because it
requires a foothold first (`AV:L/PR:L`) but executes as root. The lower score is
the more dangerous flaw in engineering terms, and a reader who ranks remediation
by score alone would fix them in the wrong order. Both are the same missing
control and should be fixed together.

Two scoring rules are applied consistently across this report, and are stated here
because both push scores *down* in ways a reader might otherwise question.

**Scope (`S`) changes only when a security authority boundary is crossed.** F-02
and F-03 are scored `S:C` because each discloses a credential that authenticates to
a *different* component under its own authority: the console leaks the telephony
application's credentials, and the telephony application leaks the automation
worker's token. F-04 is scored `S:U` despite yielding root, because the worker
already runs as root; command execution inside it stays within the authority that
component already holds and crosses nothing. A service running as root that is made
to run attacker commands is not a scope change, and inflating it to `S:C` to reach a
larger number would misreport what the metric measures.

**Impact is attributed once.** F-02 and F-03 are disclosure findings, scored
`C:H/I:N/A:N`. Reading a configuration endpoint or a voicemail alters and denies
nothing; the integrity and availability loss that follows from *using* the
disclosed credentials is scored at the finding that uses them, F-04. Scoring each
rung of the chain at `C:H/I:H/A:H` would multiply one real-world outcome across
four findings and inflate the picture.

Those two rules together give F-02 and F-03 identical vectors and therefore
identical scores (6.5). This is stated rather than disguised: both are
credential-disclosure findings reached from the same foothold, with the same access
vector, the same privilege requirement, and the same confidentiality impact. CVSS
v3.1 offers no base metric in which they differ, so the distinction between them,
that F-03 exposes a secret authorising root-level action while F-02 exposes
application credentials, is carried in the remediation roadmap rather than forced
into a score the metric does not support.

Individual findings are otherwise rated in isolation; the executive summary states
the chained outcome, full root compromise, as Critical independently of the
individual scores.

## Appendix B: Tooling

`nmap`, `curl`, browser developer tools, `ss`, `systemctl`, `chisel`. No custom or
destructive tooling was used.
