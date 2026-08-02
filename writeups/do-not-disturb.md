# Do Not Disturb

**Platform:** TryHackMe (Hacker Holidays) · **Difficulty:** Medium · **Date:** 2026-08-02
**Tags:** Web, Boot2Root, NoSQL Injection, SSTI, Node.js, Privilege Escalation

## The target

A Node.js/Express web app, "Byte Lotus Poolside," on port 80, with SSH on 22. The
briefing said someone was "already inside" and told me to "climb the way he
climbed" and recover a user flag and a root flag. A full boot2root: web foothold,
then privilege escalation to root.

## Recon

`nmap -sC -sV -p-` returned two services: SSH (22) and HTTP (80, Node/Express).
The web app was a staff/guest login. Content discovery with `gobuster`, then a
large wordlist, only ever surfaced `/staff` (403, "staff access only") and
`/logout`. Browsing issued no session cookie, and directory brute-forcing was
exhausted, so the only remaining way in was the login itself.

## Foothold 1: NoSQL authentication bypass

The login placeholder named a real account, `attendant`. Because the stack is
Node/Express, I tested for NoSQL injection rather than SQL. Sending the password
as a Mongo-style operator instead of a plain value bypassed the check:

```
username=attendant&password[$ne]=1
```

This asks the datastore for the `attendant` user "whose password is not 1", which
is always true, so it logged me in with no password and issued a signed
`connect.sid` session. Setting that cookie in the browser opened `/staff`. (The
backend was NeDB, which speaks the same operators as MongoDB, which is why the
operator injection worked.)

## Foothold 2: SSTI to remote code execution

`/staff` was a "Cabana Desk" that let staff edit a booking-confirmation template,
explicitly labelled EJS and using `<%= guest %>` syntax. An app that renders a
user-supplied template in a named engine is a server-side template injection
candidate, so I confirmed it with `<%= 7*7 %>`, which returned `49`: the server
evaluated my expression. Because EJS compiles to JavaScript, I escalated from
evaluating maths to running commands by reaching Node's `child_process` module:

```
<%= process.mainModule.require('child_process').execSync('id') %>
```

This executed as the `poolside` service account. I traded the clunky template box
for a proper reverse shell, using a non-blocking `setsid` background launch so the
synchronous `execSync` did not freeze the web server, stabilised it with a
`python3` pty, and read the user flag from poolside's home directory.

## Privilege escalation 1: exposed Node inspector (poolside to pipelinesvc)

Enumeration ruled out sudo (it wanted a password I did not have), reused
credentials, cron, and timers. A custom systemd service, `lotus-telemetry.service`,
ran as `pipelinesvc` with:

```
ExecStart=/usr/bin/node --inspect=127.0.0.1:9229 processor.js
```

The `--inspect` flag leaves Node's debugger listening, here on `127.0.0.1:9229`. A
debugger, by design, runs arbitrary code inside the target process, so an exposed
inspector is remote code execution as whoever owns that process. "Localhost only"
was no protection, because I already had a shell on the box. I attached with Node's
own client, `node inspect 127.0.0.1:9229`, and evaluated code inside the process,
which ran as `pipelinesvc`.

## Privilege escalation 2: disk group to root

Running `id` through the inspector showed `pipelinesvc` was in the `disk` group.
Membership of `disk` grants raw read/write to the block devices, which sits
underneath the filesystem's permission checks, so it is effectively root-level
file access. I used `debugfs` against the root partition (`/dev/nvme0n1p1`, found
by listing the `disk`-group devices in `/dev`) to read root's home directory
straight off the disk, bypassing its `700` permissions entirely:

```
debugfs -R "ls -l /root" /dev/nvme0n1p1
```

Reading the root flag file itself was the same `debugfs -R "cat ..."` one more
time.

## Finding & fix

Each link in the chain trusted something it should not have:

- **NoSQL injection:** the login passed raw request input into a query. Fix: cast
  inputs to strings and reject query operators in user-supplied data.
- **SSTI:** user input was compiled as a template. Fix: never render
  user-controlled templates; treat their content as data, never as code.
- **Exposed debugger:** a production service shipped with `--inspect` on. Fix:
  never enable the inspector in production; localhost binding is not a control
  once an attacker has any foothold.
- **Dangerous group:** the service account sat in `disk`, a root-equivalent group.
  Fix: least privilege; a service account should never hold raw disk access.

The through-line is the briefing's own warning. Every stage trusted an assumption
(client input, a template, a debug port, a group membership), and because an
attacker was already inside, each assumption became the next rung of the ladder.
Defence in depth means no single trusted assumption should be enough to hand over
the next account.
