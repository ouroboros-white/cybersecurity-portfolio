# Tools

Small utilities written for the assessments in [reports/](../reports/), published
here because a technique is easier to judge when the code behind it can be read.
Each one names the report it came from.

| Tool | Does | From |
|---|---|---|
| [`xor_known_plaintext.py`](xor_known_plaintext.py) | Recovers a repeating-key XOR key from a known plaintext prefix, brute forcing any key bytes the prefix does not cover | [Recoverable XOR Cryptosystem](../reports/xor-cryptosystem-2026-08.md), F-01 and F-02 |

## `xor_known_plaintext.py`

The XOR assessment turned on a single property: the target's message format
guaranteed a fixed, publicly known prefix, and XORing that prefix against the
ciphertext hands over the key one byte per position it covers. Where the prefix
was shorter than the key, the uncovered positions were small enough to brute
force outright.

The routine used during the assessment was written inline and thrown away, which
was the mistake described in that report's "What I learnt": the key regenerated
on every connection, so a result tied to one session did not transfer, and
working from a saved script was what turned a one-off decryption into a
repeatable attack. This is that script, generalised so the key length, the known
plaintext, and the brute-force alphabet are all arguments rather than assumptions
baked into the code.

```bash
python tools/xor_known_plaintext.py <hex-ciphertext> -k <key-length> -p <known-plaintext>
```

Given a five-byte key and a three-character known prefix, it recovers three key
bytes directly and searches the remaining two over 3,844 candidates:

```
[*] known plaintext covers 3/5 key bytes, brute forcing 2 over 62 candidates (3844 keys)
 -2.940  key='Sk3y7'  'the quarterly revenue summary is attached and remains confidential'
 -3.089  key='Sk3y1'  'the wuartcrly tevense sukmary&is artachcd anb remgins eonfibentigl'
```

### Two things worth reading the code for

**Ranking is frequency-based, and the first two attempts at it were wrong.**
Sorting candidates by "how much of this is printable ASCII" does not work, and
finding out why was the useful part. A wrong key still lands most bytes in the
printable range, so real text and near-miss garbage score almost identically.
Weighting punctuation below letters was worse: it actively penalises the correct
answer whenever the plaintext is punctuation-heavy, which is exactly what a
structured record looks like. Both versions ranked the correct key well down the
list. Scoring against English character frequencies puts it first in every test
case, because what separates text from noise is its distribution, not its
printability. The heuristic still assumes English and is not a language model,
so the tool prints the top several candidates and expects a human to read them.

**A contradiction means the assumption is wrong, so it is an error rather than a
guess.** A known plaintext longer than the key covers each key position more than
once. If two occurrences of the same position disagree, either the assumed key
length or the assumed plaintext is wrong, and the script says so and stops
instead of returning a confident answer built on a bad premise. Passing a correct
prefix with the wrong key length triggers exactly that.

### Limitations

Stated plainly, because the tool is narrow by design:

- It assumes the known plaintext sits at the **start** of the message. A known
  string at an unknown offset is a different problem and this does not solve it.
- Frequency scoring assumes **English**. Against another language, or against
  binary plaintext, the ranking is meaningless even though the key recovery is
  still correct.
- The brute-force cost is `len(alphabet) ** uncovered`. Two uncovered bytes over
  the default 62-character alphabet is instant; four is roughly fifteen million
  candidates and will not be. It is deliberately not parallelised, because at the
  point that matters the right move is a better known plaintext, not more cores.
- It is a cryptanalysis aid for a weak cipher used in a lab. Nothing here applies
  to a real cipher, which is the entire point of the finding it came from.

_Built with AI assistance (Claude Code). The technique, the assessment it came
from, and the review were mine._
