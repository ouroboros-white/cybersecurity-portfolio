# Pickle Rick

**Platform:** TryHackMe · **Difficulty:** Easy · **Date:** 2026-08-23
**Tags:** Web, Command Injection, Filter Bypass, Privilege Escalation, Enumeration

## The target

A Rick-and-Morty-themed web server. The objective is to find three "ingredients"
scattered across the host, starting unauthenticated from a web app. Almost the
whole chain runs through a single command-execution point, which makes it a good
study in filter bypass and enumeration discipline.

## What I tried

Recon first: `curl` the homepage and read the source, which disclosed a username.
Content discovery (gobuster) plus `robots.txt` gave a single odd string that
turned out to be the login password. Username from the page source, password from
robots.txt, and the portal opened.

Behind the login was a **command panel**: it runs OS commands and returns their
output, an unauthenticated-to-authenticated path straight into command execution.
Listing the web directory surfaced a clue file and the first ingredient.

The dead end worth recording: my first attempt to read a file with `cat` failed,
the panel returned "command disabled." `cat` was blacklisted.

## What worked

The interesting part was the **filter bypass**:

1. The panel gave arbitrary command execution as the web user.
2. `cat` was blocked, but a blacklist only stops the names it knows. I read files
   with `sed` instead (`head`, `tail`, `less`, `nl`, `strings` would all serve the
   same purpose). Blocking one command name is not a control; there is always
   another binary that does the same job.
3. Enumeration located the three ingredients: one in the web root, one in a user's
   home directory (its filename contained a space, so the path needed quoting),
   and one under `/root`.
4. The third needed root. `sudo -l` showed the web user could run any command as
   root with no password, so reading `/root` was a single `sudo` away.

## Finding & fix

Finding: the app leaked credentials (password in `robots.txt`, username in page
source), a panel allowed arbitrary OS command execution, a `cat` blacklist was
trivially bypassed with an alternative tool, and a permissive `sudo` rule
(NOPASSWD for all commands) handed over instant root.

Fix:
- Never expose an OS-command interface to user input. If commands must run, use
  strict allow-lists and parameterised calls, never a raw shell.
- Do not store credentials in `robots.txt` or page source; both are readable by
  anyone.
- Blacklisting command names is not a security control. Filter by allow-list, or
  remove the dangerous capability entirely.
- Restrict `sudo` to specific, necessary commands rather than NOPASSWD on
  everything.
