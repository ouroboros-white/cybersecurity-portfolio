# Security Assessment Report: Business-Logic and API Abuse

**Assessment type:** Black-box web-application business-logic assessment
**Environment:** TryHackMe training target (Hacker Holidays, "Towel on the Sunbed"), the "Ponzi Portfolio" rewards web application
**Assessor:** ouroboros-white
**Report date:** 2026-08-03
**Version:** 1.0
**Classification:** Public, portfolio sample

---

> **About this document.** This is a real assessment written to professional
> structure against a **lab target**, not a live client engagement. No production
> system or third party was tested. It documents a pure business-logic compromise
> of a web application to demonstrate the reporting deliverable: an attack path,
> CVSS-rated findings, detection analysis, and remediation. Target identifiers are
> redacted as they would be in a client report, and no flags are reproduced.

---

## 1. Executive summary

A Node.js web application that awards a time-limited daily reward was assessed
from an authenticated user perspective. A single **business-logic flaw** let a
user bypass the once-per-24-hours limit and grant themselves an effectively
unlimited reward balance, reaching a privileged application tier (the "Whale
Vault", intended to require sustained legitimate use) in seconds.

No injection or memory-safety bug was involved; the compromise was purely
**logical**, in how the reward claim was processed. The root cause is a **race
condition** (time-of-check to time-of-use) in the claim endpoint: the server
checked eligibility and granted the reward as two separate, non-atomic steps.
Firing many claim requests simultaneously caused them all to pass the eligibility
check before any recorded the claim, so all of them paid out. The **absence of
rate limiting** on the endpoint removed the only practical barrier to sending
them.

Individually the findings are High and Medium; in combination they allow complete
defeat of the application's core economic rule.

### Findings at a glance

| ID | Finding | Severity | CVSS 3.1 |
|----|---------|----------|:--------:|
| F-01 | Race condition (TOCTOU) in the reward-claim endpoint | **High** | 8.0 |
| F-02 | No rate limiting on state-changing endpoints | **Medium** | 5.4 |

Each finding carries a **detection analysis**: the telemetry a monitored
environment would generate. As with lab targets generally, this is written as
theory, since the application carries no instrumentation of its own.

---

## 2. Scope and rules of engagement

| Item | Detail |
|------|--------|
| **In-scope asset** | A single Node.js/Express web application (port 3000). |
| **Perspective** | Authenticated, using a self-registered guest account (registration is open). |
| **Objective** | Reach the restricted "Whale Vault" application tier and its gated reward. |
| **Excluded** | Denial-of-service, and any target outside the named application. |
| **Authorisation** | Performed within the TryHackMe platform terms, which authorise exploitation of the provided target. |
| **Window** | 2026-08-03. |

---

## 3. Methodology

The assessment followed the OWASP Web Security Testing Guide, focused on
**business-logic testing** (WSTG-BUSL). The application's API was mapped from its
own client-side script, the reward mechanism was modelled, and the concurrency
behaviour of the value-granting endpoint was tested. Severity is CVSS v3.1 base
score, mapped to CWE. Detection analysis is written as theory, since the target
is not instrumented.

**Tooling:** browser developer tools, `curl`. No custom or destructive tooling
was used.

---

## 4. Attack path

1. **Understand the economy.** A guest account was registered. The reward was 50
   units per 24 hours; the restricted tier required 150 (exactly three claims).
2. **Map the API from the client.** The client script exposed the endpoints:
   a state endpoint (`GET .../me`), the reward grant (`POST /claim`, carrying no
   client-supplied time value), and the gated reward (`GET /vault`, returned when
   the balance meets the threshold).
3. **Classify the flaw.** Because the claim request carried no client-controlled
   timestamp and the cooldown was computed server-side, time could not be
   tampered. This pointed to a **concurrency** flaw rather than a
   time-manipulation one.
4. **Exploit the race.** On a freshly registered account (eligible to claim), many
   `POST /claim` requests were sent in parallel. They all passed the eligibility
   check before any recorded the claim, raising the balance to several multiples
   of a single reward in one window.
5. **Collect.** With the balance above the threshold, the gated reward was
   retrieved from the vault endpoint.

Each step depended on understanding the application's own rules; no technical
exploit was used.

---

## 5. Detailed findings

### F-01: Race condition (TOCTOU) in the reward-claim endpoint

| | |
|---|---|
| **Severity** | **High** |
| **CVSS 3.1** | 8.0, `AV:N/AC:L/PR:L/UI:N/S:U/C:H/I:H/A:N` |
| **CWE** | CWE-367: Time-of-check Time-of-use Race Condition (and CWE-362) |
| **Affected component** | Reward-claim endpoint |
| **Status** | Open |

**Description.** The claim endpoint verified eligibility ("has the cooldown
elapsed?") and then granted the reward and recorded the claim as **separate,
non-atomic operations**. When requests arrive concurrently, they interleave
between the check and the update, so many requests observe "eligible" before any
of them writes "claimed", and every one of them grants the reward.

**Evidence (sanitised).** From a freshly registered, eligible account, a burst of
parallel `POST /claim` requests raised the account balance to several multiples of
a single reward in one cooldown window, versus the one grant the rule intends.
The inflated balance unlocked the restricted tier and its gated reward.

**Business impact.** Complete bypass of the reward-rate business rule. A user can
mint effectively unlimited in-application currency and reach privileged states
meant to gate exclusive content. In any system where the currency has real value,
this is direct financial loss and corruption of the economy's integrity.

**Detection and response (theory).** Two signals. At the request layer, a burst of
near-simultaneous, identical state-changing requests from a single session is the
signature of a race attempt. At the data layer, the reward ledger increasing
faster than the business rule allows (more than one grant inside a single cooldown
window) is a definitive, rule-based tell. Alert on per-session request bursts to
value-granting endpoints and on any rule-violating ledger delta.

**Remediation.** Make the check-and-grant **atomic**. Enforce the rule at the data
layer with a database transaction and row lock, or a single conditional update
(grant only where the recorded last-claim time is older than the window), so
concurrent requests serialise and exactly one succeeds. Never enforce a
value-granting rule with a pre-check that is separate from the action it guards.

### F-02: No rate limiting on state-changing endpoints

| | |
|---|---|
| **Severity** | **Medium** |
| **CVSS 3.1** | 5.4, `AV:N/AC:L/PR:L/UI:N/S:U/C:L/I:L/A:N` |
| **CWE** | CWE-770: Allocation of Resources Without Limits or Throttling |
| **Affected component** | Application API (state-changing endpoints) |
| **Status** | Open |

**Description.** The claim endpoint accepted unlimited rapid requests with no
throttling. This both enabled the race in F-01 (by allowing a large concurrent
burst) and would permit other automated abuse of value-granting or
authentication-related endpoints.

**Business impact.** Removes the practical barrier to concurrency and automation
attacks, directly amplifying F-01 and exposing the application to resource
exhaustion and brute-force-style abuse.

**Detection and response (theory).** High request rates per session or source IP
to state-changing endpoints are the signal; standard rate-limiting and
anti-automation telemetry catch it.

**Remediation.** Apply per-user and per-IP rate limiting to state-changing
endpoints, especially those that grant value, in combination with the atomic fix
in F-01.

---

## 6. Remediation roadmap

| Priority | Action | Findings |
|:--------:|--------|----------|
| **1 (Now)** | Make the claim check-and-grant atomic (transaction, row lock, or conditional update) | F-01 |
| **2 (Now)** | Add per-user and per-IP rate limiting to state-changing endpoints | F-02 |
| **3 (Ongoing)** | Review every "once per period" and value-granting operation for concurrency safety; treat business rules as data-layer invariants, not application-layer pre-checks | All |

---

## 7. Conclusion

The application was defeated not by a technical exploit but by a logical one: it
trusted that a "check, then act" sequence would run without interruption.
Concurrency broke that assumption. The lesson generalises to any value-granting
operation: **a business rule must be enforced as an atomic, data-layer invariant,
because any check performed separately from the action it guards can be raced.** A
single lock closes the entire class.

---

## Appendix A: Severity methodology

Severity is CVSS v3.1 base score. Bands: Critical 9.0 to 10.0, High 7.0 to 8.9,
Medium 4.0 to 6.9, Low 0.1 to 3.9. The race condition is rated with Attack
Complexity Low because the naive, unsynchronised implementation made it reliably
exploitable on the first attempt; a hardened implementation would raise complexity.

## Appendix B: Tooling

Browser developer tools and `curl`. No custom or destructive tooling was used.
