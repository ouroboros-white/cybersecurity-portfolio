# OhSINT

**Platform:** TryHackMe · **Difficulty:** Easy · **Date:** 2026-08-23
**Tags:** OSINT, BSSID Geolocation, Metadata, Username Pivoting, Reverse Image Search

## The target

A single image file and one instruction: find out everything about the person
behind it. No credentials, no service, just one artifact and an identity to
reconstruct. This is the "pull one thread until the whole identity unravels"
style of OSINT, distinct from the geolocation and metadata angles in my other
write-ups.

## What I tried

I started where any image should: metadata. `exiftool` on the file surfaced a
username in the copyright field, and that one string turned out to be the entire
key. Searching it found the same handle reused across a code-hosting profile, a
social account, and a personal blog, so the rest was a matter of visiting each
and noting what it leaked:

- the code profile gave a location and a contact email,
- the social account had posted a WiFi access-point identifier (a BSSID),
- the blog gave a current-location update and, it turned out, more than the
  author intended.

The dead end worth recording: I first read the blog's rendered pages like an
ordinary visitor and found nothing sensitive. The move that paid off was assuming
a sloppily built site hides things badly, and checking the source rather than the
page.

## What worked

Three techniques carried it:

1. **Username-reuse pivoting.** One handle, reused everywhere, unravelled the
   whole identity. This is the core OSINT truth: people reuse identifiers, and one
   is enough to chain to all the rest.
2. **BSSID geolocation.** The posted WiFi BSSID is a unique hardware identifier,
   and wardriving databases such as WiGLE map BSSIDs to physical coordinates. A
   WiFi network is not something people think of as location data, but its BSSID
   pins a place. This was the technique new to me here.
3. **Reading the source, not the page.** The blog hid a value in text styled the
   same colour as its background: invisible to a visitor, plainly present in the
   HTML. Viewing source surfaced it at once.

## Finding & fix

Finding: a full identity, a location, contact details, and a stored secret were
all recoverable from a single image, because identifiers were reused across
platforms, a hardware identifier was published openly, and sensitive text was
"hidden" with nothing but CSS.

Fix:
- Separate handles across platforms so one does not chain to the rest.
- Never publish a BSSID or other hardware identifiers; they geolocate you.
- Never rely on styling to hide data. Anything sent to the browser is in the
  source, so if it must stay secret it must not be sent to the client at all.
