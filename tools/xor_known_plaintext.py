#!/usr/bin/env python3
"""Recover a repeating-key XOR key from a known plaintext prefix.

Written for the assessment in reports/xor-cryptosystem-2026-08.md, where the
target encrypted a secret under a short repeating-key XOR and the message format
guaranteed a fixed, publicly known prefix. That prefix is the whole attack: XOR
it against the ciphertext and the key falls out, one byte per position covered.

Generalised here so it works against any repeating-key XOR where some leading
plaintext is known. Where the known prefix is shorter than the key, the
uncovered positions are brute forced over a candidate alphabet and the results
ranked, because a partial key still reduces the search to something trivial.

The point worth keeping in mind while reading this: the weakness is not that
XOR is weak. It is that XOR of a key against a plaintext an attacker can guess
hands over the key directly, and a predictable message format supplies that
guess for free.
"""

from __future__ import annotations

import argparse
import itertools
import math
import string
import sys

DEFAULT_ALPHABET = string.ascii_letters + string.digits


def xor_bytes(data: bytes, key: bytes) -> bytes:
    """XOR data against key, repeating the key across the full length."""
    return bytes(b ^ key[i % len(key)] for i, b in enumerate(data))


def recover_key_positions(ciphertext: bytes, known: bytes, key_length: int) -> dict[int, int]:
    """Derive every key byte the known plaintext covers.

    Position i of the plaintext was encrypted with key byte i % key_length, so
    each known plaintext byte discloses exactly one key byte. A prefix longer
    than the key simply confirms the same positions repeatedly, which is a
    useful consistency check: a disagreement means the assumed key length or the
    assumed plaintext is wrong.
    """
    recovered: dict[int, int] = {}
    for i, plain_byte in enumerate(known):
        if i >= len(ciphertext):
            break
        position = i % key_length
        key_byte = ciphertext[i] ^ plain_byte
        if position in recovered and recovered[position] != key_byte:
            raise ValueError(
                f"contradiction at key position {position}: the known plaintext "
                f"implies both {recovered[position]:#04x} and {key_byte:#04x}. "
                f"The key length or the known plaintext is wrong."
            )
        recovered[position] = key_byte
    return recovered


# Relative frequency of each letter and the space character in English text,
# used to rank candidate plaintexts. Frequency scoring is the standard approach
# for this and it earns its place: a simple printable-or-not test scores real
# text and near-miss garbage almost identically, because a wrong key still lands
# most bytes in the printable range. Worse, weighting punctuation below letters
# actively penalises the correct answer whenever the real plaintext is
# punctuation-heavy, which is exactly what a structured record looks like.
# Distribution, not printability, is what separates text from noise.
_ENGLISH_FREQ = {
    " ": 0.1830, "e": 0.1020, "t": 0.0750, "a": 0.0650, "o": 0.0630,
    "n": 0.0570, "i": 0.0570, "s": 0.0530, "r": 0.0500, "h": 0.0490,
    "l": 0.0330, "d": 0.0330, "u": 0.0230, "c": 0.0220, "m": 0.0200,
    "f": 0.0180, "w": 0.0170, "g": 0.0160, "y": 0.0160, "p": 0.0150,
    "b": 0.0120, "v": 0.0080, "k": 0.0060, "x": 0.0010, "q": 0.0010,
    "j": 0.0010, "z": 0.0010,
}

# Floor probability for any printable byte the table does not cover: digits,
# punctuation, and uppercase beyond its lowercased form. Small enough that a
# candidate full of them ranks below real prose, large enough that structured
# text (dates, identifiers, hyphenated records) is not thrown away.
_FLOOR_PROB = 0.0005

# Penalty for a byte outside printable ASCII. A control character in the middle
# of a candidate is near-certain evidence of a wrong key, so this dominates.
_NONPRINTABLE_PENALTY = -10.0


def printable_score(data: bytes) -> float:
    """Rank a candidate plaintext by how closely it matches English character
    frequencies, as an average log-likelihood per byte.

    Higher is better, and the values are negative, since they are logarithms of
    probabilities. A crude heuristic, and deliberately so: it is enough to sort
    candidates so a human reads the right one first. It is not a language model,
    it assumes English, and it should not be trusted to pick the answer on its
    own. Always read the top few candidates rather than taking the first.
    """
    if not data:
        return float("-inf")
    total = 0.0
    for b in data:
        if b in (9, 10, 13):
            total += math.log(_FLOOR_PROB)
        elif 32 <= b <= 126:
            total += math.log(_ENGLISH_FREQ.get(chr(b).lower(), _FLOOR_PROB))
        else:
            total += _NONPRINTABLE_PENALTY
    return total / len(data)


def candidate_keys(recovered: dict[int, int], key_length: int, alphabet: str):
    """Yield every full key consistent with the recovered positions."""
    unknown = [i for i in range(key_length) if i not in recovered]
    if not unknown:
        yield bytes(recovered[i] for i in range(key_length))
        return
    for combination in itertools.product(alphabet.encode(), repeat=len(unknown)):
        key = bytearray(key_length)
        for position, value in recovered.items():
            key[position] = value
        for position, value in zip(unknown, combination):
            key[position] = value
        yield bytes(key)


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Recover a repeating-key XOR key from a known plaintext prefix.",
    )
    parser.add_argument("ciphertext", help="ciphertext as a hex string")
    parser.add_argument(
        "-k", "--key-length", type=int, required=True,
        help="length of the repeating key, in bytes",
    )
    parser.add_argument(
        "-p", "--known-plaintext", required=True,
        help="plaintext known to appear at the start of the message",
    )
    parser.add_argument(
        "-a", "--alphabet", default=DEFAULT_ALPHABET,
        help="candidate bytes for key positions the known plaintext does not cover "
             "(default: ASCII letters and digits)",
    )
    parser.add_argument(
        "-n", "--top", type=int, default=5,
        help="number of ranked candidates to print (default: 5)",
    )
    args = parser.parse_args()

    if args.key_length < 1:
        parser.error("key length must be at least 1")

    try:
        ciphertext = bytes.fromhex(args.ciphertext.strip())
    except ValueError as exc:
        parser.error(f"ciphertext is not valid hex: {exc}")

    if not ciphertext:
        parser.error("ciphertext is empty")

    known = args.known_plaintext.encode()
    if len(known) > len(ciphertext):
        parser.error("known plaintext is longer than the ciphertext")

    try:
        recovered = recover_key_positions(ciphertext, known, args.key_length)
    except ValueError as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 1

    covered = len(recovered)
    missing = args.key_length - covered
    print(
        f"[*] known plaintext covers {covered}/{args.key_length} key bytes"
        + (f", brute forcing {missing} over {len(args.alphabet)} candidates"
           f" ({len(args.alphabet) ** missing} keys)" if missing else ""),
        file=sys.stderr,
    )

    results = [
        (printable_score(plain := xor_bytes(ciphertext, key)), key, plain)
        for key in candidate_keys(recovered, args.key_length, args.alphabet)
    ]
    results.sort(key=lambda row: row[0], reverse=True)

    for score, key, plain in results[: args.top]:
        rendered = plain.decode("ascii", errors="replace")
        print(f"{score:7.3f}  key={key.decode('ascii', errors='replace')!r}  {rendered!r}")

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
