# Security Foundations

Knowledge areas I can speak to and apply, built through a completed **Level 2
Award in Cybersecurity**, ongoing **Level 3** study, and hands-on labs. This
page is the theory counterpart to the practical record in
[TRAINING.md](TRAINING.md): it sets out what I understand and how the pieces
fit together, written to reflect current UK guidance (NCSC, ICO) rather than
dated rules of thumb.

Much of this was first developed by designing security for a fictional legal
firm end to end — threat model, access-control system, an ethical-hacking
brief, and a legal/compliance induction — then keeping each part consistent
with the others. The worked examples below come from that exercise.

## Domains at a glance

| Domain | What I can do |
|---|---|
| Threats & vulnerabilities | Classify human, digital, and physical/environmental threats and explain what makes a system vulnerable |
| Access control & identity | Design an RBAC model with least privilege, MFA, and a joiner/mover/leaver lifecycle |
| Defensive measures | Explain layered digital and physical controls and where each one actually helps |
| Offensive security | Describe the pen-test lifecycle, standard methodologies, tooling, and how findings are prioritised |
| Legal, ethical & compliance | Apply the Computer Misuse Act, Data Protection Act / UK GDPR, and the Data (Use and Access) Act 2025 |

---

## 1. Threats and vulnerabilities

A *threat* is something that can cause harm; a *vulnerability* is the weakness
it exploits. Risk is the product of how likely a threat is and how much impact
it would have — which is why a simple **likelihood × impact** score is a useful
way to decide what to fix first.

**Human factors** are the most common route to a breach — not because people
are careless, but because there are so many of them and each is a potential
entry point. This covers negligence (weak or reused passwords, shadow IT),
genuine error (a mis-sent email, a clicked link), and malicious insiders who
abuse legitimate access. Recent industry reporting continues to put the human
element behind the large majority of breaches.

**Digital and network threats** include malware (ransomware, spyware,
keyloggers, and the more destructive worms and wipers), advanced persistent
threats (well-resourced, often state-backed, patient), denial-of-service
attacks, and man-in-the-middle interception — where stealing an active session
token can sidestep MFA entirely rather than defeating it head-on.

**Physical and environmental threats** are easy to forget and disproportionately
effective: tailgating through a badged door, propped doors, and impersonation
(the "IT technician" or "delivery driver") succeed far more often than most
people assume. Add hardware theft, natural disaster, and plain infrastructure
failure, and it's clear physical security is part of cyber security, not a
separate discipline.

## 2. Access control and identity

I can design a **Role-Based Access Control (RBAC)** model: group permissions by
role rather than by individual, so access is granted for what a job needs and
nothing more (**least privilege**). RBAC is simple to administer when roles are
fairly stable — a new hire inherits the right access by being placed in a group.
It is not automatically "as secure as" Attribute-Based Access Control (ABAC);
the two suit different problems. ABAC evaluates context (device, location, time,
data sensitivity) and gives finer-grained, dynamic control at the cost of more
complexity. The right choice depends on the environment.

A worked permission matrix maps each role to each data area as full control,
read/modify, read-only, or no access. A design point I'd now emphasise:
**separation of duties**. Administrators should be able to *manage* who has
access without being able to *read* the protected content, and senior staff
should not hold blanket full control — including the right to change permissions
and delete records — simply because they are senior. Business access and
permission-administration rights are two different things and are safer kept
apart.

Around that sit the identity controls:

- **Multi-factor authentication**, ideally a hardware security key, so a
  breached password is not enough on its own.
- **Password policy in line with current NCSC guidance**: long, unique
  passwords (a password manager makes this realistic), *no* forced routine
  expiry — change on suspicion of compromise instead — and credentials stored
  **hashed and salted**, never encrypted or plain.
- **A joiner/mover/leaver lifecycle**: provision least-privilege access on day
  one, review and re-scope access when someone changes role, and on exit disable
  the account immediately, revoke keys, and end active sessions before archiving.

## 3. Defensive measures (digital and physical)

Security works in **layers (defence in depth)**: no single control is trusted to
hold, so if one is bypassed others remain. I can explain the common layers and,
importantly, their limits:

- **Endpoint protection** — signature detection for known threats, plus
  heuristic/behavioural analysis for novel ones; modern tools fold in EDR.
- **Firewalls** — inbound rules keep hostile traffic out; outbound rules stop
  data and malware getting out, which is the half people forget.
- **Encryption** — full-disk encryption protects data at rest on a lost device;
  TLS/VPNs protect it in transit; PKI and digital signatures prove authenticity.
- **Wireless** — WEP and WPA are obsolete; WPA2 (AES) and WPA3 (with the SAE
  "Dragonfly" handshake) are current. I'd be honest that hiding an SSID and MAC
  filtering are weak controls — an SSID is trivially discoverable and MAC
  addresses are spoofable — so they supplement a strong passphrase rather than
  replace it.
- **Physical** — access control (cards, keypads, biometrics), CCTV and
  personnel, centralised and hardened storage, and the reminder that a biometric,
  unlike a password, cannot be reissued once it leaks.
- **Backups** — the **3-2-1 rule** (three copies, two media, one off-site), and
  the trade-offs between full, differential, and incremental backups (speed of
  backup vs. speed and completeness of restore).

## 4. Offensive security (ethical hacking)

Ethical hacking is authorised, scoped testing that uses the same tools and
techniques as an attacker to find weaknesses first. The non-negotiable
foundation is the **scope / Rules of Engagement**: the systems, IP ranges,
domains, and times that are in bounds. Testing outside scope risks breaching the
Computer Misuse Act, and where the target holds personal data the engagement
also needs a Data Processing Agreement, since the tester acts as a data
processor.

I can describe:

- **Test styles** — open/transparent ("white box", full information) vs.
  opaque/closed ("black box", outsider's view), and the trade-off between
  coverage and realism.
- **Methodologies** — PTES (a seven-phase end-to-end standard), OSSTMM (a
  metrics-driven scientific approach), and MITRE ATT&CK (a knowledge base of
  real-world tactics and techniques, ideal for scenario-driven tests). In the UK,
  NCSC **CHECK** and industry **CREST** signal tester quality.
- **Tooling** — Nmap (host and port discovery), Wireshark (traffic capture and
  confirming data is encrypted in transit), Metasploit (exploitation framework),
  Hashcat (offline password cracking to test policy strength).
- **Prioritisation** — CVSS scores a finding 0–10 (Low 0.1–3.9, Medium 4.0–6.9,
  High 7.0–8.9, Critical 9.0–10) from factors like access required, privileges
  needed, and impact to confidentiality, integrity, and availability — turning
  "here are some findings" into "fix these first."

**Case study — NotPetya / DLA Piper (2017).** I use this to show why the
controls above matter together. NotPetya spread not through a phishing click but
through a **compromised software supply chain** — a poisoned automatic update to
Ukrainian accounting software (M.E.Doc) — then moved laterally using the
**EternalBlue** exploit against systems that had not applied a patch Microsoft
had already released. It was a *wiper* disguised as ransomware, later attributed
to the Russian military. The law firm DLA Piper was among the casualties: a flat,
unsegmented network let it spread worldwide, and email was down for days. The
lesson is a stack — patch management, network segmentation, least privilege, and
tested backups — not any single fix. Well-designed RBAC and segmentation are
meant to *contain* a compromise rather than let one account sink the whole firm.

## 5. Legal, ethical, and compliance

- **Computer Misuse Act 1990** — the core UK offences: unauthorised access
  (s.1), access with intent to commit a further offence (s.2), unauthorised acts
  impairing a system (s.3), and acts causing or risking serious damage (s.3ZA).
  These turn on **authorisation and intent** — which is exactly why staying
  inside an agreed scope matters, and why authorisation must be explicit rather
  than assumed.
- **Data Protection Act 2018 / UK GDPR** — the seven principles (lawfulness,
  fairness and transparency; purpose limitation; data minimisation; accuracy;
  storage limitation; integrity and confidentiality; and accountability).
  Consent is one lawful basis for processing, not the only one — a common
  misconception. Breaches can draw fines up to £17.5m or 4% of global turnover.
- **Data (Use and Access) Act 2025** — current legislation (Royal Assent 19 June
  2025) that updates and works alongside UK GDPR/DPA rather than replacing them:
  a clearer route for individuals to complain directly to organisations,
  clarified handling of data-access requests, and the renaming of the
  Information Commissioner's Office to the **Information Commission**.
- **Ethics** — the practical line between acceptable and unacceptable use of
  organisational systems, and why it matters: confidentiality builds client
  trust, and misuse carries both legal consequences and disciplinary ones.

---

_The name-bearing coursework these notes are drawn from is kept private;
this page is a synthesis of the underlying knowledge, corrected to current
guidance. Practical lab evidence lives in [TRAINING.md](TRAINING.md)._
