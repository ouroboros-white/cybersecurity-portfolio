# Searchlight IMINT

**Platform:** TryHackMe · **Difficulty:** Easy · **Date:** 2026-08-08
**Tags:** OSINT, IMINT, Geolocation, Reverse Image Search

## The target

A series of photographs, each with questions about where it was taken and, for
some, who operates the place or what happened there. No host, no interaction:
every answer comes from the image and open sources. The images were supplied as
screenshots, so there was no EXIF to read. That is the realistic case for
adversary-provided imagery, and it forces the work onto the visual content rather
than the metadata. The specifics are withheld here, because the answers are real
locations and one is a small business's owners and contact details. The method is
the transferable part.

This was my second IMINT room after Sakura, and I used it to turn the ad-hoc moves
from that first attempt into a repeatable checklist.

Commercially this is imagery intelligence: the same work as geolocating a photo of
a client's premises, or a staff member's holiday post, during the reconnaissance
phase of a red team or social engineering engagement.

## What I tried

I ran one loop on every image: inventory the frame, isolate the most identifiable
feature, reverse image search a tight crop of it, then confirm the candidate in
Street View. Inventorying first is the part that matters, because the feature that
geolocates a photo is rarely its subject. Systematic geolocation works off a fixed
checklist of clue classes, and I read each frame against it: the script and
language on signage, road markings and which side traffic drives on, street
furniture (bollards, signal housings, utility poles), architecture and building
materials, and vegetation as a climate and latitude constraint. The subject of the
photo is often the least useful thing in it.

One image cost me a real detour. After identifying a business, I chased a secondary
biographical lead about where one of its operators had previously worked. It was a
plausible thread and a dead end: the connection was real but led nowhere useful.
The answer came from a completely different class of source, which was the lesson I
took away. When a lead stalls, change the type of source rather than pushing harder
on the same one.

## What worked

**Reverse image search is several different engines, and the choice decides the
result.** Yandex, Google Lens, Bing Visual Search and TinEye do not do the same
thing. Yandex runs content-based image retrieval: it builds a numerical feature
descriptor of the image and matches that against near-duplicates, which makes it
strong on buildings, streetscapes and landscapes even with no text in frame.
Google Lens is built around entity and text recognition, so it excels at reading a
sign or naming a product but is weaker on an unlabelled facade. TinEye is strict
near-duplicate matching, best for finding where else an exact image appears.
Running the same crop through more than one covers their different failure modes.

**Cropping changes the match, not just the framing.** A feature descriptor is
dominated by whatever fills most of the frame. If the distinctive object is small
against a busy background, the descriptor is mostly background and the match drifts
to visually similar clutter. Cropping tight to the one identifiable element (a
sign, a sculpture, a distinctive roofline) rebuilds the descriptor around the thing
that actually locates the image. Several searches that returned nothing useful on
the full frame resolved on the first try once cropped.

**A unique named entity resolves one-to-one; a generic scene resolves one-to-many.**
The fastest images carried a brand, a landmark or a piece of wayfinding signage. A
named business geolocates to a single address; "a red-brick high street"
geolocates to a country at best. Where a frame held a named entity, the search
named the place outright and the rest of the image became confirmation rather than
search.

**Public art carries a provenance trail that a candid photo does not.** Two images
were sculptures. Public works are catalogued across tourism sites, news coverage
and artist registries, so reverse image search returned not just the location but
the piece's title, its artist, and the photographer credited on the specific image
I was handed. That is why a "who took this photo" question was answerable at all: a
snapshot has no paper trail, a commissioned public artwork does.

**Background-to-foreground: geolocate what is searchable, then derive what is not.**
The hardest image had an unsearchable subject in the foreground and a searchable
shop behind it. Locating the background shop fixed the street; the foreground
business then fell out from its position on that street. The searchable feature
does not have to be the thing the question asks about, it only has to share a
location with it.

**A trading entity is indexed across independent corpora, so pivot by source
type.** Once I had the business, mapping data was exhausted, so I switched sources
deliberately. A review platform gave the operators' forenames, and a surname came
from an unrelated community newsletter that had profiled the place. A real business
leaves traces in corpora that share nothing with each other (mapping, review sites,
directories, event listings, community PDFs), and each answers a different
question. When one runs dry the move is to change the kind of source, not to
re-query the one that ran out. Agreement between two independent sources also
raises confidence that an identification is real rather than coincidence.

**Confirm by triangulation, not on a single feature.** The river image had several
candidate buildings. Rather than guess, I fixed two independent landmarks on the
far bank, used their relative positions to establish which waterway it was and
which way the camera faced, then walked the near bank in maps until a third feature
agreed. Two independent features intersecting is an identification; one feature
that happens to match is a guess that got lucky.

## Finding & fix

**Finding:** an ordinary photograph, stripped of metadata, still yields a precise
location and from there a named individual. Background signage, a public sculpture,
or a skyline across water each fixed a location, and a location plus a business
name reached real names and contact details through public listings and reviews.
No control failed because none was applied: every link was either published
voluntarily or catalogued in passing by a third party.

**Fix:** the exposure is the background, not the geotag. Before publishing an
image, read it the way an analyst would, and ask what signage, artwork,
reflections or skyline sit behind the subject. Strip metadata as a build step
rather than a habit. A small business should assume a shopfront photo ties directly
to its listings, reviews and any third-party coverage, and that those together name
the people who run it.

For offensive work this is the reconnaissance a social engineering engagement opens
with. The value is knowing which clue classes resolve to a location, how few hops
separate a location from a named person, and therefore where a client's real
exposure sits, instead of guessing at it.
