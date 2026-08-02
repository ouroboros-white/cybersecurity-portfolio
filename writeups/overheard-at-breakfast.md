# Overheard at Breakfast

**Platform:** TryHackMe (Hacker Holidays) · **Difficulty:** Easy · **Date:** 2026-08-02
**Tags:** OSINT, Social Media, Hashing, Gravatar

## The target

A screenshot of a chat between two resort guests. From the conversation alone,
find a hidden account "nobody was supposed to find." The room is explicit: *read*
what they said, do not skim.

## What I tried

I read it twice. Two speakers: "Ponzi," posting heavily on social media and
referencing *customers* (likely staff), and "Lambo," who leaks two things: an
email address, and a description of "a free tool that let me upload my profile
and link other media accounts... started with a G... until I wiped everything."

I triaged. Ponzi and the social-media detail were distractors; Lambo's email plus
that tool description were the live thread. Googling the description landed on
Gravatar. I tried the account directly, but login needs an email verification
code and a password reset needs a verification link. Both routes go through
Lambo's Gmail, which every player attacking the room would share, so that cannot
be the intended per-player path. I refused to attack the mailbox and stayed on
the Gravatar angle.

## What worked

Gravatar's own Email Checker turned the email into its hash and a profile URL.
The hash is the crux: Gravatar identifies every profile by a hash of the account
email (SHA-256 in its current API), so "wiping everything" never unlinked Lambo.
The deterministic hash still resolves the profile. I used that one-way hash as a
lookup key, not as something to reverse. The profile carried a reward string and
even taunted that "email hashes follow you places you didn't expect." I decoded
the reward string in CyberChef (Magic identified it as Base64) to finish.

## Finding & fix

**Finding:** an email is a permanent, enumerable identity key. A hash-of-email
identifier means anyone holding the email, or just the hash seen beside a blog
comment, can pull the linked profile, and deleting content never changes the
deterministic key.

**Fix (opsec):** treat every reused identifier (email, handle, password, avatar
hash) as a cross-site bridge. Wall personas apart: a unique email per identity,
never shared between a real-name and a pseudonymous account. And remember that an
identifier is burned the moment it is public; deletion afterward is theatre.
