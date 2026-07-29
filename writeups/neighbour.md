# Neighbour

**Platform:** TryHackMe (Hacker Holidays) · **Difficulty:** Easy · **Date:** 2026-07-28
**Tags:** Web, Information Disclosure, Broken Access Control

## The target

A login page. The goal was to get in and reach the flag, starting with no
credentials.

## What I tried

The room nudged me to check the page source (view-source, Ctrl+U). That is worth
doing on any login page, because developers often leave more in the client-side
code than they intend. In the source I found guest credentials (`guest` /
`guest`) sitting in plain view, so I logged in with them.

Being a guest account, it dropped me on a low-privilege page. The URL was
structured around the role, so I reasoned the admin area might follow the same
pattern and changed the path to `/admin` directly, rather than looking for a
link to it.

## What worked

`/admin` loaded straight away and held the flag. There was no server-side check
that my guest session was actually allowed to view it: the app relied on simply
not linking the page, which is not a control at all.

## Finding & fix

Two issues chained here:

**Information disclosure:** working credentials were exposed in client-side
source. Anyone can read page source, so nothing secret belongs there.

**Broken access control:** the admin page enforced no server-side authorisation,
so a logged-in guest reached it just by guessing the URL (forced browsing).

**Fix:** never put credentials in client-side code, and enforce authorisation
on the server for every request, checking the user's role on privileged pages
rather than relying on the UI not linking them.
