# Sakura

**Platform:** TryHackMe (OSINT Dojo) · **Difficulty:** Easy · **Date:** 2026-08-07
**Tags:** OSINT, Metadata, Git Forensics, Blockchain Analysis, IMINT

## The target

An image left behind after an intrusion, and nothing else. The task was to work
from that single artefact to an attribution package: who the attacker is online,
how they were monetising access, where they physically live, and which law
enforcement body has jurisdiction. Entirely passive, with no interaction with the
target permitted or needed.

Commercially this is the recon phase of a red team engagement, or a standalone
digital footprint assessment: the same techniques, run against a client's staff
and infrastructure before any exploitation.

## What I tried

The image was an SVG, so I read its source first. Two things were in there: a
wall of binary in `aria-label` attributes, and editor metadata left behind by
the graphics package used to build it.

I chased the binary. That was the dead end, and it was designed to be one. It
decoded to a taunt telling me the words were worthless. The real content was the
metadata: the export path carried a Linux `/home/` directory, and the directory
name of a home folder *is* a username. Editor metadata as an identity leak is
the lesson; the decoding was theatre.

That username pivoted to a code-hosting profile, and there I made the second
mistake. I worked from the pinned repositories on the profile page and concluded
there was nothing further. The header said nine repositories; five were pinned.
Pinned repositories are the ones the account owner chose to display, not a list
of what exists. Everything the task needed was in the four I had not opened. The
lesson generalises well beyond this platform: where a page shows a selected
subset, go and find the full listing.

Two smaller errors worth keeping: I once submitted a block height where a
service name was asked for, and I correctly identified a Japanese prefecture but
attached it to the wrong question. Both were caught by checking the answer
against the question's noun and the expected format before submitting, a habit
I did not have at the start of the room and did by reflex by the end.

I also had two answers spoiled by a search engine's AI summary. Unsourced
answers are worthless in an investigation, because "a model told me" does not
survive a client asking how you know. I re-derived both from the artefacts and
changed how I search.

## What worked

Four techniques carried the whole chain.

**Editor metadata.** Design tools stamp absolute filesystem paths into exported
files. The path contains the author's OS username.

**PGP key parsing.** A public key block is not opaque. It is structured packets
under ASCII armour, one of which is a User ID packet holding whatever name and
email the creator typed at generation time. Read it locally rather than pasting
a target's key material into a third-party site:

```bash
gpg --show-keys publickey
```

`--show-keys` parses and prints without importing to the keyring. The output
gives the UID, plus creation and expiry dates. The creation date here matched the
day of the intrusion, corroborating the timeline from a completely separate
artefact.

**Git history.** Git is append-only: removing a secret and committing writes a
*new* commit recording the removal. The old value stays readable in the diff
forever, in the web UI, no clone required. Go to the repository, then commits,
and read the messages before the diffs, because people write things like "Update
miningscript" and tell you which commit to open.

The attacker did not delete the live mining configuration, they replaced it with
a placeholder, which acted as a field-by-field legend for the line it removed:

```
stratum://ethwallet.workerid:password@miningpool:port
```

Aligning the red line against that green one labels every component: wallet
address, worker ID, credential, pool hostname, port. Three of the section's four
answers came off that single diff. The pool hostname also parses right-to-left
like any domain, where the registrable domain names the organisation and the
subdomain is just which regional server they connected to.

**Blockchain analysis.** A wallet address goes straight into a public block
explorer. The address format itself identifies the chain, which picks the
explorer. Two things about reading the result: transactions are **directional**,
and native currency transfers sit on a different tab from **token** transfers.
A question about "another cryptocurrency" on this chain means a token, so the
default transaction view will never show it.

Incoming transfers were labelled with the mining pool, independently confirming
what the config file said. Outgoing transfers reached a labelled exchange, and
that is the one that matters: pools are anonymous, but exchanges are regulated
businesses holding KYC records, so an outbound transfer is where a pseudonymous
address becomes a subpoena target. The `FUNDED BY` field, every wallet's first
inbound transaction, is a further lead in its own right.

**Imagery geolocation.** Holiday photos on a secondary social account gave a
departure city, an airline lounge and a final approach. Three different methods:
a landmark identified by eye from the background; branded interior signage run
through reverse image search (Google Lens returned two independent matches
naming the same terminal, which is what made it safe to commit to rather than
guess between that airline's hubs); and a satellite screenshot matched by panning
a real coastline until the shape agreed. Season and vegetation were also
load-bearing, since blossom in full bloom in January is itself a geographic
constraint.

**Wardriving data.** SSID and BSSID are different things: the former is the
human-readable name, the latter the access point's MAC address. Volunteers drive
around logging both against GPS and upload them to public databases, so a
network name can be resolved to a hardware identifier *and* street-level
coordinates through Advanced Search, narrowed by country. Those coordinates then
answered the home city question in the following section, which is the synthesis
the room was actually teaching.

A captured list of saved networks is worth calling out separately: every entry
is a place the device has been. A school lab, a fast-food chain, a municipal
free-WiFi network named after the city that operates it. That is a movement
history, and the municipal entry corroborated the coordinates independently.

## Attack chain

```mermaid
flowchart TD
    A["SVG left at scene"] --> B["Editor metadata"]
    B --> C["OS username"]
    C --> D["Code-hosting profile"]
    D --> E["Deleted commit"]
    D --> F["PGP key UID"]
    E --> G["Mining config"]
    G --> H["Block explorer"]
    F --> I["Secondary persona"]
    I --> J["Travel photos"]
    I --> K["Saved SSID list"]
    K --> L["Wardriving lookup"]
    J --> M["Home city"]
    L --> M
    M --> N["National referral"]
```

## Finding & fix

**Finding:** a complete identity and physical address were assembled from
published data alone. Every link in the chain was either volunteered by the
target (file metadata, committed secrets, holiday photos, a personally named
home network) or logged in passing by a third party. Nothing was compromised
and no control failed, because no control was ever applied to any of it.

**Fix:** four controls, each cheap. Strip metadata before publishing any file,
as a build step rather than a habit. Treat a committed secret as burned and
*rotate* it; deleting and re-committing hides it from the file, never from the
history. Keep separated personas actually separated, since one cross-reference
collapses both. And name wireless networks with strings that identify nothing,
because an SSID containing a person, family or company name is a public,
permanent geolocation beacon in databases nobody thinks to check.

**Analytical note:** the persona name appeared in four independent artefacts and
was self-asserted in all four. Corroboration between self-assertions raises
confidence, not proof. The honest phrasing is "the persona identifies as", and
the referral rests on location, which was externally sourced.
