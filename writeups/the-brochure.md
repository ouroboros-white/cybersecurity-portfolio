# The Brochure

**Platform:** TryHackMe (Hacker Holidays) · **Difficulty:** Easy · **Date:** 2026-07-28
**Tags:** OSINT, Encoding

## The target

An open-source intelligence challenge. The goal was to find the flag by
following a trail from the hotel's public web presence out into social media.

## What I tried

The lab site gave me the hotel's brand name, so I treated that as my starting
lead and searched for it in the open (on my own machine, not the lab box). The
search turned up an Instagram account for the hotel.

That account had a single follower, an account called "Vera". One follower is
unusual and deliberate, so it stood out as the next step rather than noise. I
opened Vera's profile and found three images, each carrying a chunk of encoded
text. The strings had the look of base64 rather than plain writing, so I treated
them as encoded data rather than trying to read them directly.

## What worked

I collected the text from all three images and concatenated it in order, then
decoded the combined string with CyberChef. Base64 is an encoding, not
encryption, so it reverses cleanly with no key. The decoded output was the flag.
The intended path was the pivot chain (main site to brand name to Instagram to
the one odd follower to the images), not any single clever trick.

## Finding & fix

**Finding:** sensitive data was recoverable through open sources: a linked
social account leaked it, and it was only base64-encoded, which is trivially
reversible and offers no real protection.

**Fix:** treat social media as part of the attack surface and keep sensitive
data off it. Never rely on base64 to hide anything, since it is encoding, not
encryption. Reducing the public OSINT footprint removes the trail entirely.
