# Towel on the Sunbed

**Platform:** TryHackMe (Hacker Holidays) · **Difficulty:** Medium · **Date:** 2026-08-03
**Tags:** Web, Business Logic, Race Condition, API Abuse

## The target

A Node.js "Ponzi Portfolio" rewards web app. You claim 50 PONZI every 24 hours;
reach 150 to unlock the "Whale Vault" and its flag. The briefing hinted at a gap
"between his request and the server's clock", and that the clock was "the only
thing checking him".

## What I tried

This was my first time exploiting a race condition, so the reasoning that got me
there mattered more than the exploit. I registered a guest account and explored. Out of habit I ran `nmap` and
`gobuster` first, which confirmed Node/Express but found nothing else, and that
was the point: for a **business-logic** bug the network layer was never going to
hold the answer, so I dropped scanning and read the app.

The real recon was the client. Reading `dashboard.js` mapped the whole API: a
state endpoint (`GET /dashboard/api/me`), the reward grant (`POST /claim`), and
the gated reward (`GET /vault`, returned when balance reaches 150). The tell was
what the claim request *didn't* carry: no timestamp, no client-controlled time
value at all. The `/me` response showed the cooldown was computed server-side. My
first instinct had been the old game trick of changing the clock, but the server
owned its own clock, so time could not be tampered. That ruled out time
manipulation and pointed squarely at **concurrency**.

## What worked

The server checks "can you claim?" and then grants and records the claim as
separate steps. So I raced it. On a *fresh* account (eligible to claim, window
still open), I fired many `POST /claim` requests in parallel. They all passed the
eligibility check before any of them recorded the claim, so every one paid out.
Balance jumped to 400 (eight claims through a single window), tier flipped to
"Whale", and `GET /vault` returned the flag. The briefing's "claimed three times
over" was literal.

## Finding & fix

**Finding:** a time-of-check-to-time-of-use race condition in the reward-claim
endpoint. The eligibility check and the reward grant were not atomic, so
concurrent requests all saw "eligible" and all paid out, bypassing the
once-per-24h rule. The absence of rate limiting removed the only barrier to
sending the burst.

**Fix:** make the check-and-grant **atomic**. Enforce the rule at the data layer
with a transaction and row lock, or a single conditional update that grants only
where the recorded last-claim time is older than the window, so concurrent
requests serialise and exactly one succeeds. Add rate limiting. Treat business
rules as data-layer invariants, never as application-layer pre-checks, because any
check performed separately from the action it guards can be raced.
