# Detection Rules

Sigma rules written from behaviour I observed while carrying out the assessments
in [reports/](../reports/), rather than copied from a rule repository. Each rule
names the report and finding it came from, so the offensive work and the
defensive artefact can be read against each other.

Sigma is a vendor-neutral detection format: the logic is written once in YAML and
converted to the target platform's query language with `sigma convert`.

## Rules

| File | Rules | Detects | From |
|---|---|---|---|
| [`ssh_bruteforce_then_success.yml`](ssh_bruteforce_then_success.yml) | 4 | SSH password brute force, and the brute force that succeeded | [Network Share to Root](../reports/smb-to-multiuser-compromise-2026-08.md), F-02 |

### Why that file holds four rules

The rules escalate rather than duplicate, because the same log source answers
three different questions and they do not carry the same urgency.

| Rule | Level | What it means |
|---|---|---|
| `ssh_failed_password` | informational | One failed password. Ordinary noise, never alerted on directly. |
| `ssh_accepted_password` | informational | One successful password login. Ordinary, never alerted on directly. |
| `ssh_bruteforce_burst` | high | Ten or more failures for one account from one source in five minutes. Someone is guessing. |
| `ssh_bruteforce_success` | critical | A burst followed within ten minutes by a success for that same account and source. Someone guessed correctly and is now logged in. |

The last rule is the one that matters, and it is the sequence that actually
occurred during the assessment: the host enforced neither lockout nor rate
limiting, so the wordlist attack ran uninterrupted until it worked. An attempt
gets triaged when an analyst has time. A success is an active intrusion.

## Validation and conversion support

`sigma check` reports 0 errors and 0 issues across all four rules.

Conversion was tested rather than assumed, and the results are mixed. This
matters, because "Sigma is vendor-neutral" describes the format, not the state of
every backend.

| Target | Base rules | `event_count` correlation | `temporal_ordered` correlation |
|---|:--:|:--:|:--:|
| Splunk SPL | yes | yes | no |
| Elasticsearch Lucene | yes | no | no |
| Elasticsearch ES\|QL | no | no | no |
| Kusto (Sentinel) | yes | no | no |

Only the Splunk backend converts correlation rules at all, and even it does not
yet support temporal correlation. The generated SPL for the burst rule is
committed at
[`converted/ssh_bruteforce_burst.splunk.spl`](converted/ssh_bruteforce_burst.splunk.spl)
so the output can be read directly. The ES|QL failure is a separate issue: that
backend rejects keyword-style string matching, which is what these rules use
because they cannot assume the log pipeline has already parsed sshd messages into
fields.

The practical reading is that the critical rule here is currently a portable
statement of intent rather than something that drops into a SIEM unaided. On a
platform without temporal correlation it would be implemented natively, using the
Sigma rule as the specification.

## Honesty note

These rules are written against the log formats the techniques produce, and the
logic is reviewed and validated, but they have not been run against a live SIEM
with production data volumes. The false-positive notes in each rule are reasoned
expectations rather than measured rates, and the thresholds (ten failures, five
minutes, ten minutes) are defensible starting points rather than tuned figures.
Tuning is environment-specific work that cannot be done from a lab.
