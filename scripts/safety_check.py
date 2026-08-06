"""
safety_check.py

Last line of defence before anything is committed to a public repo.

Scans the files that the sync is about to publish for material that must
never end up public: credentials, session tokens, private keys, CTF flags,
email addresses, and local filesystem paths that leak your real name.

Design note - why this isn't just a keyword grep:

    TryHackMe room titles and descriptions legitimately contain words like
    "password", "authentication", "token" and "credential" (there is a room
    literally called "Authentication Bypass"). A scanner that flags those
    would fire on every single sync, and a check that always fails is a
    check everyone learns to ignore.

    So instead:
      - JSON *keys* are checked against credential-shaped names, because a
        key called "password" means a stored secret, whereas the word
        "password" in a description is just a topic.
      - *Values* are checked against secret-shaped patterns (flag formats,
        PEM headers, bearer tokens, emails, home directory paths) that
        prose does not normally contain.

Exit codes:
    0 - nothing suspicious found, safe to commit
    1 - findings reported, commit should be aborted
"""
import json
import os
import re
import subprocess
import sys

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

# Every tracked file is scanned, not a hand-maintained list.
#
# This used to name three files - the ones the sync rewrites - and that was
# wrong. Everything committed to a public repo is published, whether the
# sync touched it or not, and a hand-maintained list silently stops
# covering files added later. A real local path (C:\Users\<name>) sat in
# SETUP.md for days precisely because SETUP.md was not on the list.
FALLBACK_TARGETS = [
    "data/thm_data.json",
    "README.md",
    "TRAINING.md",
]

# Scanning the scanner would match its own pattern literals.
SELF = "scripts/safety_check.py"

SKIP_SUFFIXES = (".png", ".jpg", ".jpeg", ".gif", ".ico", ".pdf", ".zip")


def tracked_files() -> list:
    """List files git is tracking, falling back to a fixed list if git is absent."""
    try:
        result = subprocess.run(
            ["git", "ls-files"],
            cwd=BASE_DIR, capture_output=True, text=True, check=True,
        )
    except (OSError, subprocess.CalledProcessError):
        return FALLBACK_TARGETS
    return [
        line for line in result.stdout.splitlines()
        if line and line != SELF and not line.lower().endswith(SKIP_SUFFIXES)
    ]

# JSON keys that indicate a stored secret, regardless of their value.
#
# Keys are normalised before matching because TryHackMe's API is camelCase
# throughout (earnedAt, rarityTier, imageURL) - so a leaked secret would
# realistically arrive as "sessionToken", not "session_token". Normalising
# strips separators and splits camelCase, letting one term list cover
# sessionToken, session_token, SESSION-TOKEN and friends alike.
SENSITIVE_SUBSTRINGS = (
    "password", "passwd", "secret", "token", "apikey", "authorization",
    "cookie", "bearer", "privatekey", "credential", "sessionid", "accesskey",
)
# Short terms that would false-positive as substrings ("auth" inside
# "authorName") are matched as whole words only.
SENSITIVE_WORDS = {"pwd", "auth", "key", "salt", "hash", "signature"}


def normalise_key(key: str) -> tuple:
    """Return (joined, words) forms of a key for matching."""
    spaced = re.sub(r"[_\-\s]+", " ", str(key))
    spaced = re.sub(r"(?<=[a-z0-9])(?=[A-Z])", " ", spaced)
    words = spaced.lower().split()
    return "".join(words), set(words)


def is_sensitive_key(key: str) -> bool:
    joined, words = normalise_key(key)
    if any(term in joined for term in SENSITIVE_SUBSTRINGS):
        return True
    return bool(words & SENSITIVE_WORDS)

# Patterns that look like an actual secret or piece of PII in a value.
VALUE_PATTERNS = [
    ("CTF flag", re.compile(r"(?i)\b(?:thm|htb|flag|ctf)\{[^}\n]{2,}\}")),
    ("private key block", re.compile(r"-----BEGIN (?:[A-Z ]+ )?PRIVATE KEY-----")),
    ("bearer token", re.compile(r"(?i)\bbearer\s+[A-Za-z0-9._\-]{20,}")),
    ("email address", re.compile(r"[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}")),
    ("Windows user path", re.compile(r"(?i)[A-Z]:\\+Users\\+[^\\\s\"'/]+")),
    ("Unix home path", re.compile(r"(?:/home/|/Users/)[A-Za-z0-9._-]+")),
    ("flag file reference", re.compile(r"(?i)\b(?:user|root)\.txt\b")),
]


# Fictional accounts that appear as *content* in a write-up - the victim host's
# username in a DFIR room, for example - are not a leak of the assessor's
# identity, which is what the user-path patterns guard against. They are
# allow-listed by name so a path carrying the assessor's real username is still
# caught: the real name is deliberately NOT listed here (listing it would leak it
# in this public file), so any user path not on this short, vetted list still
# fails the check. Add a name here only after confirming it is room/lab content.
CONTENT_USERNAMES = {"sophie"}


def is_exempt(label: str, snippet: str) -> bool:
    """Known-safe matches that would otherwise be noise.

    noreply addresses (git's actions@users.noreply.github.com, and the
    co-author trailers) are non-contactable and non-identifying by design -
    that is the entire point of the noreply convention - so flagging them
    trains the reader to skim past real findings.

    Windows/Unix user paths are exempt only when the trailing username is a
    vetted content account (CONTENT_USERNAMES). A path bearing the assessor's
    real username is not on that list and still fails.
    """
    if label == "email address" and "noreply" in snippet.lower():
        return True
    if label in ("Windows user path", "Unix home path"):
        username = re.split(r"[\\/]+", snippet)[-1].lower()
        return username in CONTENT_USERNAMES
    return False


def scan_text(text: str, where: str, findings: list) -> None:
    for label, pattern in VALUE_PATTERNS:
        for match in pattern.finditer(text):
            snippet = match.group(0)
            if is_exempt(label, snippet):
                continue
            if len(snippet) > 60:
                snippet = snippet[:57] + "..."
            findings.append(f"{where}: {label} -> {snippet}")


def scan_json(node, path: str, findings: list) -> None:
    """Walk a parsed JSON structure, checking keys and string values."""
    if isinstance(node, dict):
        for key, value in node.items():
            here = f"{path}.{key}" if path else key
            if is_sensitive_key(key) and value not in (None, "", [], {}):
                findings.append(f"{here}: credential-shaped key holding a value")
            scan_json(value, here, findings)
    elif isinstance(node, list):
        for index, item in enumerate(node):
            scan_json(item, f"{path}[{index}]", findings)
    elif isinstance(node, str):
        scan_text(node, path or "<root>", findings)


def main() -> None:
    findings = []
    scanned = 0

    for relative in tracked_files():
        full_path = os.path.join(BASE_DIR, relative)
        if not os.path.exists(full_path):
            continue
        try:
            with open(full_path, "r", encoding="utf-8") as f:
                raw = f.read()
        except (UnicodeDecodeError, OSError):
            continue  # not text; nothing here for a pattern scan to read
        scanned += 1

        if relative.endswith(".json"):
            try:
                scan_json(json.loads(raw), "", findings)
            except json.JSONDecodeError as exc:
                findings.append(f"{relative}: file is not valid JSON ({exc})")
        else:
            for line_number, line in enumerate(raw.splitlines(), start=1):
                scan_text(line, f"{relative}:{line_number}", findings)

    if findings:
        print("Safety check FAILED - refusing to publish. Findings:", file=sys.stderr)
        for finding in findings:
            print(f"  - {finding}", file=sys.stderr)
        print(
            "\nReview the above. If a finding is a false positive, adjust the "
            "patterns in scripts/safety_check.py deliberately - do not skip "
            "the check.",
            file=sys.stderr,
        )
        sys.exit(1)

    print(f"Safety check passed ({scanned} file(s) scanned).")


if __name__ == "__main__":
    main()
