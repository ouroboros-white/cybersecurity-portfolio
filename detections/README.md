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
| [`webservice_command_injection.yml`](webservice_command_injection.yml) | 4 | Command injection at two privilege tiers, and the evasion that defeats the naive version of the second rule | [Command-Injection Chain](../reports/command-injection-chain-2026-08.md), F-01 and F-04 |
| [`azure_credential_chain.yml`](azure_credential_chain.yml) | 3 | Versioned Key Vault secret reads, service-principal vault access, SAS-authenticated storage enumeration | [Azure Cloud Attack Chain](../reports/cloud-attack-chain-azure-2026-08.md), F-01 to F-03 |

Three log sources across the three files, which is deliberate. Linux
authentication logs, Linux process creation, and Azure resource logs answer
different questions and fail in different ways, and the third file is the one
that shows where this approach stops working.

### Why the SSH file holds four rules

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

### The command-injection rules, and writing a rule against your own evasion

The Command-Injection Chain assessment exploited **one weakness at two privilege
tiers**: user input concatenated into a shell command, first in the public web
application and again in a root-privileged export worker. The rules follow that
structure, and the escalation is carried by *what the parent process is* rather
than by what the child is.

| Rule | Level | What it means |
|---|---|---|
| `webservice_shell_child` | high | The web service account started a shell. A request-serving process has no ordinary reason to do this. |
| `webservice_recon_child` | high | The web service account ran `id`, `whoami`, or similar. Separate from the rule above, because injection into a non-shell exec path produces this without ever spawning a shell. |
| `root_worker_unexpected_child` | critical | The root worker started something other than `tar`. Identical behaviour to the first rule, one privilege tier up, so it is immediate root compromise. |
| `tar_execution_flags` | high | `tar` invoked with a flag that runs an arbitrary command. |

The fourth rule exists because the third one is defeatable, and finding that is
the most useful thing in this file.

`root_worker_unexpected_child` works by allowing the one child the worker
legitimately needs and alerting on everything else. That reads as sound until you
notice the assumption underneath it: that executing an arbitrary command requires
executing an arbitrary *binary*. It does not. `tar` has at least three flags that
run a supplied command as a side effect of archiving, including
`--checkpoint-action=exec=` and `--to-command`. An attacker injecting into the
worker's `report` field does not need to escape `tar` at all. They stay inside it,
the command executes as root, and the child process is exactly the one the rule
was told to expect. The allowed-child approach is defeated by the allowed child.

`tar_execution_flags` closes that path, and the pairing is the point: an
allowlist of processes has to be accompanied by scrutiny of how the allowed
processes can themselves be turned into interpreters, or it only detects
attackers who did not think about it.

### The Azure rules, and where Sigma runs out

These three rules convert cleanly on every backend tested, and two of them are
still weaker detections than the SSH or process-creation rules. That is not a
tooling failure. It is a property of what the underlying findings actually look
like in a log, and it is worth stating plainly rather than presenting three rules
as three equivalent controls. The table below is ordered strongest detection
first rather than in file order, because that ordering is the point.

| Rule | Level | What it means |
|---|---|---|
| `azure_sas_container_enumeration` | medium | A blob listing authenticated by a Shared Access Signature. A correctly scoped write-only token produces no list operations at all. |
| `azure_keyvault_versioned_secret_read` | high | A secret read pinned to an explicit version. Rotation exists so that callers read the current value, so pinning is unusual by construction. |
| `azure_keyvault_first_seen_identity` | informational | A service principal reading a vault. Not an alert: the malicious call and the legitimate one are identical, and only a baseline separates them. |

**`azure_sas_container_enumeration` is a real detection.** A correctly scoped
write-only SAS produces no list operations at all, so a SAS-authenticated listing
is a genuine mismatch between what the token can do and what the application
does. This one stands on its own.

**`azure_keyvault_versioned_secret_read` is close to a real detection, with one
honest gap.** The finding is that reading a *superseded* secret version discloses
a value that rotation was supposed to retire. Sigma cannot express "not the
current version": that requires knowing which version is current, which is state
the rule does not have and cannot query. The rule matches any explicitly
versioned read instead, and rests on the argument that legitimate automation does
not pin versions, because a pinned application would break at the next rotation.
That argument is sound and the rule is deployable, but it is an argument rather
than a guarantee, and an environment with version-pinned callers will need them
filtered by identity.

**`azure_keyvault_first_seen_identity` is a hunting query and is labelled
informational for that reason.** The finding it comes from is a stolen service
principal used to reach a vault. The malicious access and a legitimate one are
*the same API call by the same identity*; the only thing separating them is that
this identity had never touched this vault before. "First time seen" is not
something a stateless signature can express in any rule language. Deployed as
written it fires on all service-principal vault access, which is useless as an
alert, so it is not presented as one. It becomes a detection only when paired
with an identity-to-vault baseline, which is the platform's job rather than the
rule's.

Writing these three was the most instructive part of this work. The offensive
findings in the Azure chain are as serious as the ones in the SSH chain, and two
of the three resist signature detection almost entirely, because cloud credential
abuse mostly consists of authorised API calls made by a legitimate identity. The
detection has to come from *baseline deviation*, not from matching the request.
A portfolio that showed only the SSH rules would imply detection engineering is
more uniformly tractable than it is.

## Validation and conversion support

`sigma check` reports 0 errors and 0 issues across all eleven rules in the three
files.

One of those issues was worth chasing rather than silencing. The tactic tag for
Defense Evasion was rejected as invalid, in both the hyphenated and underscored
spellings that older rule sets use. The cause is that ATT&CK has since split that
tactic, and the version of pysigma in use here validates against the current
vocabulary, in which the relevant tactic is `stealth`. The tag is now correct
rather than merely accepted, which is the difference between validation being
useful and being a formality.

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

**Every rule in the two newer files converts on all four backends**, including
the ES|QL backend that rejects the SSH rules. The reason is worth naming, because
it is the same trade-off seen from the other side: those rules match named fields
(`User`, `Image`, `ParentImage`, `OperationName`) rather than raw event text, so
they assume the log pipeline has already parsed events into fields. That
assumption is what makes them portable, and it is also what makes them dependent
on a correctly configured source. Portability was bought with a prerequisite, not
gained for free.

Two more generated queries are committed so the output can be read directly:
[`converted/root_worker_unexpected_child.splunk.spl`](converted/root_worker_unexpected_child.splunk.spl),
which shows the allowed-child negation alongside the rule that covers its
evasion, and
[`converted/azure_keyvault_versioned_secret_read.kusto.kql`](converted/azure_keyvault_versioned_secret_read.kusto.kql).

## Reading the generated Splunk query

The committed SPL maps line for line back to the YAML: the quoted string is the
base rule, `bin _time span=5m` is the timespan, the `stats ... by` clause is the
group-by, and the final `search` is the threshold. Three properties of that
output are worth stating, because they are limitations of the detection rather
than of the format.

**The time buckets are fixed, not sliding.** `bin` divides time into rigid
five-minute blocks. Nine failed attempts at 12:04:59 followed by nine more at
12:05:01 is eighteen attempts in two seconds, and this query catches neither,
because they fall either side of a bucket boundary. That is an evasion path
against my own rule. A sliding window closes it, implemented in Splunk with
`streamstats` over a time window in place of `bin`.

**The grouping assumes fields the search does not create.** The search matches
raw event text, but the grouping is by `user` and `src_ip`, which exist only if
the platform has already parsed sshd messages into fields. A correctly configured
`linux_secure` sourcetype provides them. This is the concrete cost of keyword
matching described above.

**There is no index or sourcetype constraint.** The query was generated with
`--without-pipeline`, so it omits the environment-specific mapping that a
production query would carry (`index=... sourcetype=linux_secure`). It
demonstrates the logic; it is not a query to schedule as-is.

## Honesty note

These rules are written against the log formats the techniques produce, and the
logic is reviewed and validated, but they have not been run against a live SIEM
with production data volumes. The false-positive notes in each rule are reasoned
expectations rather than measured rates, and the thresholds (ten failures, five
minutes, ten minutes) are defensible starting points rather than tuned figures.
Tuning is environment-specific work that cannot be done from a lab.

Two further limits apply to the newer files. The service accounts, worker path,
and expected child process in `webservice_command_injection.yml` are the values
from the assessed target; they are environment specific and must be set before
the rules are used anywhere else. And the rules are not uniformly strong: as set
out above, one of the three Azure rules is a hunting query rather than an alert
and is labelled informational so it cannot be mistaken for one. Presenting eleven
rules as eleven working detections would be the easy claim and the wrong one.
