# Management Wants a Word

**Platform:** TryHackMe · **Difficulty:** Hard · **Date:** 2026-08-10
**Tags:** Forensics, Windows, DPAPI, Chrome Credentials, VeraCrypt

## The target

A KAPE triage collection pulled from a guest laptop left behind after an early
checkout, registered to a user named Vera: the SAM, SYSTEM and SECURITY registry
hives, her user profile, a full Chrome profile, and one 100 MB file in Documents
called `backup` with no extension. The goal was to reach whatever `backup` was
hiding. This was unfamiliar ground for me. My recon strength is network and
service enumeration, and this was recon of a Windows artifact tree instead, a
terrain whose map I had never walked. I am naming that up front, because working
through the unfamiliarity was the point of the room.

## What I tried

I started where I was comfortable, by fingerprinting the odd file. Fixed size, no
header, high entropy, sitting in a profile named Vera, with the hint pointing at
"1.26.29." That reads as a VeraCrypt container before any tool confirms it, so the
real question became where the password was. Chrome's `Login Data` held a saved
credential for the vault, but the password was stored as an encrypted `v10` blob,
and `backup` was encrypted too, so I followed the browser side.

I recovered Vera's Windows login as an autologon secret from the hives, then used
it to decrypt her DPAPI master key. Then I got stuck. I had the master key and
tried to decrypt the password with it directly, and it failed. The failure was the
lesson: the `v10` prefix meant the password was AES-GCM, and its key was not the
master key. I had walked past a layer.

## What worked

Reading the whole room as nested keys, each one wrapping the next. Vera's password
unwraps the DPAPI master key. The master key unwraps an AES key stored in Chrome's
`Local State`. That AES key, not the master key, decrypts the `v10` password. Once
I inserted the missing Local State layer, the credential fell out, and it opened
the VeraCrypt container natively through `cryptsetup`, mounted read-only to keep
the evidence intact. Five keys, each one's plaintext the next one's key. I let the
tooling collapse the middle steps once I understood what they were doing, rather
than before.

## Finding & fix

**Finding:** the browser saved a credential the user never typed anywhere else,
and the secrecy of the entire disk collapsed to one thing, the local login
password, which the machine stored itself through autologon. The container was
strong; the key chain around it was not. Recovery needed no cracking beyond that
one stored password, only patient unwrapping. It is the same confused-deputy shape
as the Stay Noticed assessment: a system's own stored trust became the thing that
betrayed it.

**Fix:** do not leave an autologon `DefaultPassword` in the LSA store, because it
turns a recovered triage image into full DPAPI recovery. Treat browser-saved
passwords as plaintext to anyone who reaches the profile plus that login. Anything
that actually needs to stay secret belongs behind a passphrase that lives in a
person's memory, not one recoverable from the same disk. Full-disk encryption
would have stopped the profile being readable offline in the first place.
