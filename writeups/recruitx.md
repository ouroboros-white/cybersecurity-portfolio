# RecruitX

**Platform:** TryHackMe · **Difficulty:** Easy · **Date:** 2026-08-24
**Tags:** Web, Broken Access Control, IDOR, Authorisation, File Upload, RCE

## The target

A single web application, RecruitX, an internal recruitment portal, black-box
from an unauthenticated start. No host to break into: one Apache/PHP site on port
80, and the whole engagement lives in the web tier. The goal was code execution
on the server. What made it worth writing up is that no single bug here is
exotic. Three ordinary weaknesses chained together turn "self-service job portal"
into "remote shell", which is the actual lesson.

## What I tried

Content discovery first. `gobuster` mapped the surface and returned the shape of
the app: `/admin`, `/api`, `/config`, `/uploads`, plus the expected
`register.php` and `login.php`. So I registered an ordinary account to see the
application from the inside, the way any candidate would.

The first thing I tried was lazy on purpose, to rule it out: I registered with
the username `admin`, on the off chance the app keyed anything off the name. It
did not. The account came back with role `candidate` regardless, which told me
something more useful than a win would have: **the role is assigned server-side
and is a real field**, so there is a privilege boundary here worth attacking
rather than a name check to spoof.

From the dashboard, my profile lived at `profile.php?id=7`. An `id` in the URL is
the oldest question in web testing, so I changed it. `id=1` returned a different
user's full profile, Sarah Mitchell, role `administrator`. Walking the numbers
enumerated the whole user base and, more importantly, the role ladder:
`candidate`, `hiring_manager`, `administrator`. That is horizontal authorisation
broken, an IDOR: one user reading another's data by editing a reference the
server never checks ownership of.

Then I looked at cookies, and this was the find of the box. Alongside the session
cookie, the application had set `isSarah=true`, with `HttpOnly` disabled so page
scripts (and I) can read and write it. `isSarah` maps directly to Sarah Mitchell,
the administrator. The app is deciding admin identity from a boolean cookie the
client fully controls. Separately, navigating straight to `/admin` as my
candidate account simply worked. Whether the gate is the trusted cookie, a
missing role check on the endpoint, or both, the effect is the same: a
candidate-level user reaches the admin panel. That is vertical, function-level
authorisation broken.

## What worked

The admin panel held an "Upload Company Documents" form, and that was the way to
code execution.

The form advertised `accept=".pdf,.docx,.jpg,.png"`, but `accept` is a
client-side hint to the browser's file picker, not a server-side control. The
real question is what the server validates on receipt, and the answer was: not
the file type. A test file with a `.phtml` extension uploaded cleanly and, when
requested from `/uploads/documents/`, executed as PHP. `.phtml` matters here
because Apache is configured to run it as PHP, so it sails past any filter that
only blocks `.php` whilst still executing as code.

From there it was a standard webshell: a one-line PHP file passing
`$_GET["cmd"]` to `shell_exec`, uploaded the same way, then triggered with a
command in the query string. It returned `www-data`. Remote code execution,
achieved not through a memory-corruption exploit but by walking through three
front doors that were each left unlocked:

1. IDOR to learn the users and the role model.
2. Broken function-level access control (and a client-trusted `isSarah` cookie)
   to reach the admin-only upload.
3. Unrestricted file upload to drop and run code.

One discipline note worth recording. After the objective, I enumerated for a path
to root, empty `config`, no reused credentials for the `qa` system account, no
planted escalation. This is a guided web-exploitation room scoped to the web
chain, and recognising that the target was not built to go further, rather than
grinding a box past its design, is part of the method. The engagement ends at
RCE because that was the finding.

## Finding & fix

Finding: three chained authorisation and validation failures. Object references
are not checked for ownership (IDOR), admin functions trust a client-controlled
cookie and are reachable by a low-privilege role, and file uploads are validated
only in the browser, allowing an executable `.phtml` to be written to a
web-served directory and run as code.

Fix:
- Enforce authorisation server-side on every object and every function. Check
  that the logged-in user owns the requested `id` and holds the required role.
  Never derive identity or privilege from a client-supplied cookie like
  `isSarah`; trust only the server-side session.
- Validate uploads on the server: allow-list by content type, not the
  browser `accept` attribute, store uploads outside the web root or on a host
  that never executes them, and randomise stored filenames.
- Detection opportunities a defender would have: sequential `id` values hitting
  `profile.php` from one session (IDOR enumeration), a `candidate`-role session
  reaching `/admin`, and the loud one, a `.phtml` (or any script extension)
  appearing in an uploads directory immediately followed by a web request to it.
  That last pattern is a high-fidelity webshell signature.
