# Detection Rules

Sigma rules written from behaviour I observed while carrying out the assessments
in [reports/](../reports/), rather than copied from a rule repository. Each rule
names the report and finding it came from, so the offensive work and the
defensive artefact can be read against each other.

Sigma is a vendor-neutral format: a rule here is converted to the target query
language (Splunk SPL, Elastic, Sentinel KQL and others) with `sigma convert`.

| Rule | Detects | From |
|---|---|---|
| [`ssh_bruteforce_then_success.yml`](ssh_bruteforce_then_success.yml) | A burst of failed SSH password attempts against one account from one source | [Network Share to Root](../reports/smb-to-multiuser-compromise-2026-08.md), F-02 |

**A note on honesty.** These rules are written against the log formats the
techniques produce, and the logic is reviewed, but they have not been run
against a live SIEM with production data volumes. Treat the false-positive notes
in each rule as reasoned expectations rather than measured rates. Tuning
thresholds is environment-specific work that cannot be done from a lab.
