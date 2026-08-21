"""
render_writeups.py

Builds the index table at the top of writeups/README.md from the metadata
header of each write-up, so the folder listing is never the only thing a
visitor sees.

Every write-up carries a header like:

    # Packed Light
    **Platform:** TryHackMe (...) - **Difficulty:** Easy - **Date:** 2026-07-30
    **Tags:** Network Forensics, PCAP Analysis, Cryptography

Those tags are the technical signal, and they are invisible from the GitHub
directory listing because the file names are room names. This script surfaces
them, grouped by discipline.

Only the region between the <!--INDEX:START--> and <!--INDEX:END--> markers is
touched. Everything outside those markers is hand-written and preserved.
"""

import os
import re
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
REPO_ROOT = os.path.dirname(HERE)
WRITEUPS_DIR = os.path.join(REPO_ROOT, "writeups")
README_PATH = os.path.join(WRITEUPS_DIR, "README.md")

START = "<!--INDEX:START-->"
END = "<!--INDEX:END-->"

SKIP_FILES = {"README.md", "TEMPLATE.md"}

# Ordered most specific first: a write-up lands in the first category whose
# tag set it matches. The Guestbook is tagged both Web and AI, and the AI
# angle is the interesting one, so AI is tested before Web.
CATEGORIES = [
    ("AI and LLM Security", {"AI", "LLM Security", "Prompt Injection", "LLM01"}),
    ("Cloud", {"Cloud", "AWS", "Azure"}),
    ("OSINT", {"OSINT", "IMINT"}),
    ("Digital Forensics and Blue Team", {
        "Forensics", "Network Forensics", "DFIR", "Blue Team", "PCAP Analysis",
    }),
    ("Web Application", {"Web"}),
]
FALLBACK_CATEGORY = "Other"

DIFFICULTY_ORDER = {"hard": 0, "medium": 1, "easy": 2, "info": 3}
DIFFICULTY_CELL = {
    "hard": "Hard",
    "medium": "Medium",
    "easy": "Easy",
    "info": "Info",
}

TITLE_RE = re.compile(r"^#\s+(.+?)\s*$", re.MULTILINE)
DIFFICULTY_RE = re.compile(r"\*\*Difficulty:\*\*\s*([A-Za-z]+)")
DATE_RE = re.compile(r"\*\*Date:\*\*\s*(\d{4}-\d{2}-\d{2})")
TAGS_RE = re.compile(r"\*\*Tags:\*\*\s*(.+?)\s*$", re.MULTILINE)


def parse_writeup(path: str) -> dict:
    """Pull the metadata header out of one write-up."""
    with open(path, "r", encoding="utf-8") as f:
        head = f.read(2000)

    title = TITLE_RE.search(head)
    difficulty = DIFFICULTY_RE.search(head)
    date = DATE_RE.search(head)
    tags = TAGS_RE.search(head)

    name = os.path.basename(path)
    if not (title and difficulty and tags):
        raise ValueError(
            f"{name} is missing part of its metadata header (needs a '# Title' "
            f"line, '**Difficulty:**' and '**Tags:**'). See TEMPLATE.md."
        )

    return {
        "file": name,
        "title": title.group(1),
        "difficulty": difficulty.group(1).lower(),
        "date": date.group(1) if date else "",
        "tags": [t.strip() for t in tags.group(1).split(",") if t.strip()],
    }


def categorise(entry: dict) -> str:
    tags = set(entry["tags"])
    for label, markers in CATEGORIES:
        if tags & markers:
            return label
    return FALLBACK_CATEGORY


def sort_key(entry: dict):
    """Hardest first, then most recent."""
    return (
        DIFFICULTY_ORDER.get(entry["difficulty"], 9),
        entry["date"] and _negated_date(entry["date"]),
        entry["title"].lower(),
    )


def _negated_date(date: str) -> str:
    # Invert the digits so a plain ascending sort puts recent dates first.
    return "".join(str(9 - int(c)) if c.isdigit() else c for c in date)


def build_index(entries: list) -> str:
    grouped = {}
    for entry in entries:
        grouped.setdefault(categorise(entry), []).append(entry)

    order = [label for label, _ in CATEGORIES] + [FALLBACK_CATEGORY]
    lines = []

    total = len(entries)
    disciplines = sum(1 for label in order if grouped.get(label))
    lines.append(
        f"**{total} write-ups across {disciplines} disciplines.** Each one is a "
        f"challenge solved without a walkthrough. Hardest first."
    )
    lines.append("")

    for label in order:
        bucket = grouped.get(label)
        if not bucket:
            continue
        bucket.sort(key=sort_key)
        lines.append(f"### {label}")
        lines.append("")
        lines.append("| Write-up | Focus | Difficulty | Date |")
        lines.append("| --- | --- | --- | --- |")
        for entry in bucket:
            link = f"[{entry['title']}]({entry['file']})"
            focus = ", ".join(entry["tags"])
            diff = DIFFICULTY_CELL.get(entry["difficulty"], entry["difficulty"])
            lines.append(f"| {link} | {focus} | {diff} | {entry['date']} |")
        lines.append("")

    return "\n".join(lines).rstrip()


def write_section(path: str, section: str, label: str) -> None:
    if not os.path.exists(path):
        sys.exit(f"{label} not found at {path}.")

    with open(path, "r", encoding="utf-8") as f:
        content = f.read()

    if START not in content or END not in content:
        sys.exit(
            f"{label} is missing the {START} / {END} markers. Add them where "
            f"the generated index should go."
        )

    pattern = re.compile(re.escape(START) + r".*?" + re.escape(END), re.DOTALL)
    with open(path, "w", encoding="utf-8") as f:
        f.write(pattern.sub(f"{START}\n{section}\n{END}", content))

    print(f"Updated {label}.")


def main() -> None:
    if not os.path.isdir(WRITEUPS_DIR):
        sys.exit(f"No writeups directory at {WRITEUPS_DIR}.")

    entries = []
    for name in sorted(os.listdir(WRITEUPS_DIR)):
        if not name.endswith(".md") or name in SKIP_FILES:
            continue
        entries.append(parse_writeup(os.path.join(WRITEUPS_DIR, name)))

    if not entries:
        sys.exit("No write-ups found to index.")

    write_section(README_PATH, build_index(entries), "writeups/README.md")
    print(f"Indexed {len(entries)} write-ups.")


if __name__ == "__main__":
    main()
