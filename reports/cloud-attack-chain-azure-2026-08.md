# Security Assessment Report: Azure Cloud Attack Chain

**Assessment type:** Credentialed black-box Azure cloud assessment (low-privilege start)
**Environment:** TryHackMe training target (Hacker Holidays, "CryptoCabana"), an Azure-hosted seed-phrase backup application
**Assessor:** ouroboros-white
**Report date:** 2026-08-04
**Version:** 1.0
**Classification:** Public, portfolio sample

---

> **About this document.** This is a real assessment written to professional
> structure against a **lab target**, not a live client engagement. No production
> system or third party was tested. It documents a cloud identity-and-access
> compromise to demonstrate the reporting deliverable. Resource names, tokens, and
> credentials are redacted as they would be in a client report; no flags are
> reproduced.

---

## 1. Executive summary

An Azure-hosted web application (the "kiosk"), backed by Azure Storage and Azure
Key Vault, was assessed from a **low-privilege authenticated user with no
resource-management permissions.** Despite that deliberately weak starting point,
a secret held in Key Vault was fully recovered by chaining **four ordinary cloud
misconfigurations.**

The chain: the application's front-end embedded a **hardcoded, over-permissioned
Storage SAS token**; that token granted **read and list across the entire storage
account**; the storage held a **service principal's credentials**; the service
principal held **Key Vault access the user did not**; and the target Key Vault
secret, though "rotated," still **served its original value from version history.**

No single step was sophisticated. The compromise came from trusting the client
with a credential, storing credentials where that credential could read them, and
treating rotation as if it were deletion. The chained real-world outcome is full
disclosure of the protected secret.

### Findings at a glance

| ID | Finding | Severity | CVSS 3.1 |
|----|---------|----------|:--------:|
| F-01 | Hardcoded, over-permissioned SAS token in client-side code | **High** | 7.5 |
| F-02 | Privileged credentials stored in attacker-readable blob storage | **High** | 8.6 |
| F-03 | Secret "rotation" leaves the original value readable in version history | **Medium** | 6.5 |

**Attack chain at a glance** (severity-highlighted for a management audience):

```mermaid
flowchart LR
    S["Low-privilege<br/>Azure user"] --> F1["F-01<br/>Hardcoded SAS<br/>in client JS · HIGH"]
    F1 --> F2["F-02<br/>SP credentials in<br/>readable storage · HIGH"]
    F2 --> F3["F-03<br/>Secret value live in<br/>version history · MEDIUM"]
    F3 --> R["Protected Key Vault<br/>secret disclosed"]
    classDef high fill:#c2410c,stroke:#7c2d12,color:#ffffff;
    classDef med fill:#a16207,stroke:#713f12,color:#ffffff;
    classDef term fill:#1f2937,stroke:#111827,color:#ffffff;
    class F1,F2 high;
    class F3 med;
    class S,R term;
```

Each finding carries a **detection analysis** describing expected detection
opportunities, since the lab environment carries no monitoring of its own.

---

## 2. Scope and rules of engagement

| Item | Detail |
|------|--------|
| **In-scope assets** | One Azure subscription: a Storage account (static website + blob containers) and a Key Vault. |
| **Perspective** | Credentialed, starting as a **low-privilege user** with no management-plane (ARM) permissions. |
| **Objective** | Recover the sensitive secret held in the Key Vault. |
| **Excluded** | Denial-of-service, and any resource outside the provided subscription. |
| **Authorisation** | Performed within the TryHackMe platform terms, which authorise exploitation of the provided target. |
| **Window** | 2026-08-04. |

### Target assets

| Attribute | Detail |
|-----------|--------|
| **Cloud platform** | Microsoft Azure (single subscription) |
| **Tenant / subscription** | Redacted, as it would be in a client report |
| **In-scope resources** | Storage account (static website + blob containers); Azure Key Vault |
| **Starting identity** | Low-privilege Entra ID user, no management-plane (ARM) permissions |
| **Assessment date** | 2026-08-04 |

---

## 3. Methodology

The assessment followed a standard cloud-attack workflow: enumerate the granted
identity, pivot to what the application itself trusts, follow each credential to
the next resource, and recover the objective. Tooling was the **Azure CLI** (`az`)
via Cloud Shell, plus browser developer tools. Severity is CVSS v3.1 base score,
mapped to CWE. Detection analysis describes expected detection opportunities,
since the target is not instrumented.

---

## 4. Attack path

```mermaid
flowchart TD
    A["Low-priv Azure user (no resource-list rights)"] --> B["Static website front-end / client JS"]
    B --> C["Hardcoded SAS token (blob: read + list, whole account)"]
    C --> D["List containers; find unlisted 'vault'"]
    D --> E["Service principal credentials stored in a blob"]
    E --> F["Authenticate as the service principal"]
    F --> G["Key Vault access the user lacked"]
    G --> H["Read superseded secret version = the real value"]
```

1. **Enumerated as the granted user.** `az resource list`, `az storage account
   list`, and `az keyvault list` all returned empty: the user had no
   management-plane rights. This reframed the approach from "enumerate as myself"
   to "what does the application trust to reach storage?"
2. **Read the static site front-end.** Its client-side JavaScript embedded a
   Storage **SAS token**, scoped to blob service at service/container/object level
   with **read and list** permissions and a far-future expiry, where the app only
   needed write access to one container.
3. **Used the SAS to list containers**, revealing a container **not referenced by
   the site**.
4. **Read that container**, which held a **service principal credential file** and
   a decoy secret.
5. **Authenticated as the service principal**, gaining **Key Vault access the user
   lacked**.
6. **Listed the Key Vault secrets.** The target secret's current value was a decoy
   note stating it had been rotated.
7. **Retrieved the secret's previous version**, recovering the real value.

Each rung depended on the one before it; none required elevated starting access.

---

## 5. Detailed findings

### F-01: Hardcoded, over-permissioned SAS token in client-side code

| | |
|---|---|
| **Severity** | **High** |
| **CVSS 3.1** | 7.5, `AV:N/AC:L/PR:N/UI:N/S:U/C:H/I:N/A:N` |
| **CWE** | CWE-798: Use of Hard-coded Credentials |
| **Affected component** | Storage static website (client-side JavaScript) |
| **Status** | Open |

**CVSS rationale.** `AV:N/PR:N` because the token is embedded in a public web page
and usable by any anonymous visitor with no authentication; `C:H` for full read of
the storage account, with `I:N/A:N` and `S:U` as impact stays within the storage
resource itself.

**Description.** The static web application embedded a Storage Shared Access
Signature (SAS) token as a constant in its client-side JavaScript, so any visitor
who loads the page obtains it. The token was scoped to the blob service at
service, container, and object level, with **read and list** permissions and an
expiry years in the future, where the application only required **write** access
to a single container.

**Evidence (sanitised).** The SAS appeared in the site's front-end script and,
used from the command line, successfully listed and read every container in the
storage account.

**Business impact.** Full read of the entire storage account by any anonymous
visitor, including any credentials or data stored there (see F-02).

**Expected detection opportunities.** Storage diagnostic logs would show read and
list operations spanning many containers from a single SAS, a pattern inconsistent
with the application's write-only purpose. Alert on SAS activity that exceeds the
operations the application legitimately performs.

**Remediation.** Never embed storage credentials in client-side code. Route writes
through a backend, or issue short-lived **user-delegation** SAS tokens scoped to
write-only, a single container, and a minutes-to-hours expiry.

### F-02: Privileged credentials stored in attacker-readable blob storage

| | |
|---|---|
| **Severity** | **High** |
| **CVSS 3.1** | 8.6, `AV:N/AC:L/PR:N/UI:N/S:C/C:H/I:N/A:N` |
| **CWE** | CWE-522: Insufficiently Protected Credentials |
| **Affected component** | Blob storage container |
| **Status** | Open |

**CVSS rationale.** `PR:N` because the credentials are reachable with the anonymous
SAS from F-01; `S:C` (scope changed) because the stored credentials unlock a
*separate* resource (Key Vault) beyond the storage account; `C:H` for exposure of
privileged credentials.

**Description.** A service principal's credentials (client id, secret, tenant) were
stored as a blob in the storage account, readable via the SAS from F-01. Those
credentials granted access to a separate Azure Key Vault, crossing a trust
boundary (hence the scope change in the score).

**Evidence (sanitised).** A credential file in a storage container, reachable with
the F-01 token, was used to authenticate as the service principal and reach the
Key Vault the assessing user could not. The credential file even carried a note
instructing that it be rotated if it ever left the vault; it had left, and had not
been rotated.

**Business impact.** Lateral movement from storage into Key Vault, a different and
more sensitive resource. A stored credential is a standing key waiting to be read.

**Expected detection opportunities.** Azure AD sign-in logs would show the service
principal authenticating from an unusual location or context relative to its
automation baseline. Alert on service-principal sign-ins that deviate from that
baseline.

**Remediation.** Never store credentials in storage. Use a **managed identity** so
no secret exists to steal. Immediately rotate any credential that may have been
exposed.

### F-03: Secret "rotation" leaves the original value readable in version history

| | |
|---|---|
| **Severity** | **Medium** |
| **CVSS 3.1** | 6.5, `AV:N/AC:L/PR:L/UI:N/S:U/C:H/I:N/A:N` |
| **CWE** | CWE-212: Improper Removal of Sensitive Information Before Storage or Transfer |
| **Affected component** | Azure Key Vault secret |
| **Status** | Open |

**CVSS rationale.** `PR:L` because reading version history requires the secret-read
access obtained earlier in the chain; `C:H` because the superseded version still
discloses the real sensitive value; `S:U` as the impact is confined to the Key
Vault secret.

**Description.** The target Key Vault secret had been "rotated" by writing a new
current value, but Azure Key Vault **retains every prior version and serves it on
request.** The original, sensitive value remained fully readable to anyone with
secret-read access.

**Evidence (sanitised).** The secret's current version was a placeholder note;
listing the secret's versions and reading the previous version returned the real,
sensitive value.

**Business impact.** Rotation was relied on to contain a leak but did not, because
the leaked value stayed live in version history. A "we rotated it" response is a
false sense of safety.

**Expected detection opportunities.** Key Vault diagnostic logs would record a
`SecretGet` against a non-current version, which is unusual for legitimate
automation (which reads current values). Alert on any access to a superseded
secret version.

**Remediation.** Treat rotation as insufficient for a *leaked* secret. Disable or
delete superseded versions, and invalidate the value at its source (revoke the
key/credential) rather than only writing a new current value over it.

---

## 6. Remediation roadmap

| Priority | Action | Findings |
|:--------:|--------|----------|
| **1 (Now)** | Remove the SAS token from client code; move writes to a backend or a least-privilege user-delegation SAS | F-01 |
| **2 (Now)** | Remove credentials from storage; switch to a managed identity; rotate the exposed service principal | F-02 |
| **3 (Now)** | Disable/delete superseded Key Vault secret versions; revoke the leaked value at source | F-03 |
| **4 (Ongoing)** | Enforce least privilege on all identities and SAS tokens; audit storage for stored secrets | All |

---

## 7. Conclusion

A protected secret was recovered from a low-privilege starting point through four
commonplace cloud mistakes, chained so each unlocked the next: a credential handed
to the client, a credential stored where the first could read it, and a "rotation"
that hid the leaked value rather than destroying it. The unifying lesson is a cloud
restatement of a familiar principle: **an application's identities and tokens must
carry only the access they need, and a leaked secret is not contained until it is
revoked at the source, not merely superseded.**

---

## Appendix A: Severity methodology

Severity is CVSS v3.1 base score. Bands: Critical 9.0 to 10.0, High 7.0 to 8.9,
Medium 4.0 to 6.9, Low 0.1 to 3.9. Individual findings are rated in isolation; the
executive summary notes that the chained outcome (full disclosure of the protected
secret) is the real-world impact.

## Appendix B: Tooling

Azure CLI (`az`) via Azure Cloud Shell, and browser developer tools. No custom or
destructive tooling was used.
