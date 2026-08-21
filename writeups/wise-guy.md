# Wise Guy

**Platform:** TryHackMe · **Difficulty:** Easy · **Date:** 2026-08-21
**Tags:** Cryptography, XOR, Known-Plaintext, Python

## The target

A networked "prove you are wise" service on TCP 1337, handed out with its Python
source. On connect it sends a hex string it claims hides flag 1, then asks for the
encryption key; supply the right key and it returns flag 2. The source shows the
encoding is a repeating-key XOR with a random five-character key generated per
connection.

## What I tried

I read the source before touching the service. My first reading was wrong: I
thought the key used to encrypt and the key checked against my answer were derived
differently. Re-reading, they are the same value within a connection, so I dropped
that line of thinking. The subtleties that actually mattered were two: the
hardcoded flag in the downloaded source is a redaction (the live server holds the
real one), and the key is regenerated randomly on **every** connection.

Dead ends worth recording, because they were where the time went:

- I typed Python straight into the bash prompt and got syntax errors, then typed
  into a fresh interpreter that had forgotten my variables. The lesson stuck: the
  interactive prompt forgets state the moment it closes, so the work belongs in a
  file that remembers.
- I solved one captured ciphertext, then reconnected and submitted that same key.
  It failed, because the key rotates per connection. The service even hands out a
  deliberate troll flag for a wrong key, which briefly looked like success.

## What worked

A known-plaintext attack on the repeating-key XOR. XOR is reversible: for a given
position, `plaintext XOR ciphertext = key`. Every THM flag begins `THM{`, so
XORing those four known plaintext bytes against the first four ciphertext bytes
returned four of the five key characters immediately. The key alphabet is letters
and digits (62 options), so the one remaining character was a 62-way brute force:
rebuild the full key for each candidate, decode the whole ciphertext, and keep the
single result that closed with `}` and read as sensible leetspeak.

Flag 2 was the same idea run live. Because the key rotates each connection, I had
to recover the *current* session's key from its own ciphertext and submit it
before the socket closed. That was now trivial: knowing the full plaintext of flag
1, any five consecutive known plaintext bytes yield the entire key in one XOR, no
brute force at all. Capture the session hex in one terminal, derive the key in
another, paste it back into the still-open connection.

## Finding & fix

**Finding:** a repeating-key XOR "cipher" with a short key and structurally known
plaintext is not encryption. A four-character known prefix leaks most of a
five-character key, and the residue is a trivial brute force; with any full
key-length of known plaintext there is no brute force at all.

**Fix:** never design a bespoke cipher. Use a vetted authenticated construction
such as AES-GCM with a full-length random key, and never rely on the secrecy of a
short key to protect data whose format is already known to the attacker.
