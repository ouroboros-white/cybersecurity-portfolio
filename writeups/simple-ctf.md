# Simple CTF

**Platform:** TryHackMe · **Difficulty:** Easy · **Date:** 2026-08-23
**Tags:** Web, SQL Injection, CVE, Hash Cracking, Privilege Escalation, GTFOBins

## The target

A single Linux host, black-box, goal web-application to root. The scan showed
anonymous FTP, an Apache server on port 80, and, notably, SSH moved off its
default port to a high one. My first full network-to-root chain in this folder.

## What I tried

`nmap -sC -sV -p-` set the shape: two services below port 1000 (FTP, HTTP) and
SSH relocated to a non-standard high port, worth remembering, because the login
step later depends on knowing that.

The web server's `robots.txt` disclosed a path hinting at an OpenEMR install, so
I chased it. It 404'd. The robots file turned out to be a recycled default with
that entry appended, a **deliberate rabbit hole**. Content discovery found the
real application at a different path: a CMS whose version I read straight off the
page footer and its Generator meta tag.

The dead end worth recording: I anchored on the robots.txt hint and burned time
on a path that did not exist. My own enumeration, not the hint, found the actual
app. The lesson generalises: a planted hint is not ground truth, and when a hint
and content discovery disagree, trust what is actually served.

## What worked

Three linked steps, recon to root:

1. **Version-matched to a known SQL injection.** The CMS version tied to a public
   unauthenticated SQLi (CVE-2019-9053). The exploit runs a **blind, time-based**
   injection: it cannot read data from the page, so it asks the database yes/no
   questions and infers each answer from response timing, reconstructing the
   account's hash and salt one character at a time.
2. **Cracked the salted hash offline.** With the hash and salt recovered, a
   dictionary attack found the password. Salting means each candidate word has to
   be hashed with the stolen salt before comparing, it slows an attacker but does
   not save a weak password.
3. **Foothold then privilege escalation.** The recovered credentials logged in
   over SSH on the non-standard port. `sudo -l` then showed the account could run
   a text editor as root with no password. Editors can spawn shell commands, and
   a shell spawned from a root process is a root shell, the classic GTFOBins sudo
   abuse. That was the whole escalation.

## Finding & fix

Finding: an outdated CMS carried a public SQL injection that exposed credentials,
a weak password fell to a wordlist, and an over-permissive `sudo` rule (NOPASSWD
on a shell-capable editor) turned a low-privilege user into root.

Fix:
- Patch or replace the outdated CMS; the injection is fixed in later releases.
- Enforce strong passwords, so a recovered hash does not fall to a dictionary.
- Never grant `sudo` on programs that can spawn a shell (editors, pagers,
  interpreters). Scope sudo to specific, non-shell commands. GTFOBins is the
  catalogue of why a single editor entry equals full root.
