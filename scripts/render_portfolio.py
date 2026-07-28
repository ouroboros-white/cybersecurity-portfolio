"""
render_portfolio.py

Renders two files from data/thm_data.json:

  README.md    - a short, recruiter-facing snapshot (counts, recent badges,
                 a pointer to the full history). Deliberately compact: a
                 wall of 45 room rows buries the things a human actually
                 wants to read first.
  TRAINING.md  - the complete evidence log (every room, every badge).

In both files only the region between the <!--THM:START--> and
<!--THM:END--> markers is touched. Everything outside those markers -
your bio, projects, contact details, notes - is left exactly as you
wrote it, every time this runs.
"""
import json
import os
import re
from collections import Counter
from datetime import datetime

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DATA_PATH = os.path.join(BASE_DIR, "data", "thm_data.json")
README_PATH = os.path.join(BASE_DIR, "README.md")
TRAINING_PATH = os.path.join(BASE_DIR, "TRAINING.md")

START = "<!--THM:START-->"
END = "<!--THM:END-->"

DIFFICULTY_EMOJI = {"info": "ℹ️", "easy": "🟢", "medium": "🟡", "hard": "🔴", "insane": "⚫"}
# Hardest first: the most demanding work should be the first thing a reader
# meets, not something they have to scroll past 30 intro rooms to find.
DIFFICULTY_ORDER = ["insane", "hard", "medium", "easy", "info"]

RECENT_BADGE_COUNT = 5


def natural_key(title: str) -> list:
    """Sort key that treats digit runs as numbers.

    Keeps room series together and in human order - "Part 1, Part 2,
    Part 10" rather than the "Part 1, Part 10, Part 2" you get from a
    plain alphabetical sort.
    """
    return [
        int(chunk) if chunk.isdigit() else chunk
        for chunk in re.split(r"(\d+)", title.lower())
    ]


def format_date(iso_string: str) -> str:
    """Turn an ISO timestamp into a plain YYYY-MM-DD, or '' if unparseable."""
    if not iso_string:
        return ""
    try:
        return datetime.fromisoformat(iso_string.replace("Z", "+00:00")).strftime("%Y-%m-%d")
    except ValueError:
        return ""


def difficulty_cell(difficulty: str) -> str:
    emoji = DIFFICULTY_EMOJI.get(difficulty, "")
    return f"{emoji} {difficulty}".strip() or "—"


def room_link(room: dict) -> str:
    title = room.get("title", "Unknown room")
    code = room.get("code", "")
    return f"[{title}](https://tryhackme.com/room/{code})" if code else title


def build_readme_section(data: dict) -> str:
    """Compact snapshot for the front page."""
    username = data["username"]
    rooms = data.get("rooms") or []
    badges = data.get("badges") or []

    counts = Counter(r.get("difficulty", "") for r in rooms)
    breakdown = " · ".join(
        f"{DIFFICULTY_EMOJI.get(d, '')} {counts[d]} {d}"
        for d in DIFFICULTY_ORDER
        if counts.get(d)
    )

    lines = [
        f"**Profile:** [{username}](https://tryhackme.com/p/{username})  ",
        f"**Last synced:** {data['last_synced_utc']}",
        "",
        "| Rooms completed | Badges earned |",
        "|---|---|",
        f"| {data['rooms_completed']} | {data['badge_count']} |",
        "",
    ]

    if breakdown:
        lines += [f"**Room difficulty:** {breakdown}", ""]

    recent = badges[:RECENT_BADGE_COUNT]
    if recent:
        lines.append("**Recent badges:** " + " ".join(
            f"`{b.get('title', b.get('name', 'badge'))}`" for b in recent
        ))
        lines.append("")

    lines.append("Full room-by-room history and badge log: [TRAINING.md](TRAINING.md)")
    return "\n".join(lines)


def build_training_section(data: dict) -> str:
    """The complete evidence log."""
    username = data["username"]
    rooms = data.get("rooms") or []
    badges = data.get("badges") or []

    lines = [
        f"**Profile:** [{username}](https://tryhackme.com/p/{username})  ",
        f"**Last synced:** {data['last_synced_utc']}",
        "",
        f"## Completed rooms ({len(rooms)})",
        "",
        "_Hardest first. Within each tier, related rooms are kept together._",
    ]

    # Only carry a Type column once there is actually a mix of types.
    # While every room is a "walkthrough" the column just repeats one word
    # down the page; it earns its place as soon as challenges/CTFs appear.
    show_type = len({r.get("type", "") for r in rooms}) > 1

    # Group by difficulty, then order the groups hardest-first. Any
    # difficulty the API introduces that we don't know about still gets
    # rendered - it just sorts to the end rather than vanishing.
    by_difficulty = {}
    for room in rooms:
        by_difficulty.setdefault(room.get("difficulty", "") or "unspecified", []).append(room)

    known = [d for d in DIFFICULTY_ORDER if d in by_difficulty]
    unknown = sorted(d for d in by_difficulty if d not in DIFFICULTY_ORDER)

    for difficulty in known + unknown:
        group = sorted(by_difficulty[difficulty], key=lambda r: natural_key(r.get("title", "")))
        emoji = DIFFICULTY_EMOJI.get(difficulty, "")
        heading = f"{emoji} {difficulty.title()}".strip()
        lines += [
            "",
            f"### {heading} ({len(group)})",
            "",
            "| Room | Type |" if show_type else "| Room |",
            "|---|---|" if show_type else "|---|",
        ]
        for room in group:
            if show_type:
                lines.append(f"| {room_link(room)} | {room.get('type', '') or '—'} |")
            else:
                lines.append(f"| {room_link(room)} |")

    lines += ["", f"## Badges ({len(badges)})", ""]
    if badges:
        lines += ["| Badge | Earned | Rarity |", "|---|---|---|"]
        for badge in badges:
            title = badge.get("title", badge.get("name", "badge"))
            earned = format_date(badge.get("earnedAt", "")) or "—"
            tier = badge.get("rarityTier", "")
            percent = badge.get("rarityPercent")
            if tier and percent is not None:
                rarity = f"{tier} ({percent}%)"
            else:
                rarity = tier or "—"
            lines.append(f"| {title} | {earned} | {rarity} |")
    else:
        lines.append("_No badges recorded yet._")

    return "\n".join(lines)


def write_section(path: str, section: str, label: str) -> None:
    if not os.path.exists(path):
        raise SystemExit(
            f"{label} not found at {path}. Create it with a "
            f"{START} / {END} pair where the generated section should go."
        )

    with open(path, "r", encoding="utf-8") as f:
        content = f.read()

    if START not in content or END not in content:
        raise SystemExit(
            f"{label} is missing the {START} / {END} markers. Add them at "
            "the point where the auto-generated section should appear, "
            "then re-run."
        )

    pattern = re.compile(re.escape(START) + r".*?" + re.escape(END), re.DOTALL)
    with open(path, "w", encoding="utf-8") as f:
        f.write(pattern.sub(f"{START}\n{section}\n{END}", content))

    print(f"{label} updated.")


def main() -> None:
    with open(DATA_PATH, "r", encoding="utf-8") as f:
        data = json.load(f)

    write_section(README_PATH, build_readme_section(data), "README.md")
    write_section(TRAINING_PATH, build_training_section(data), "TRAINING.md")


if __name__ == "__main__":
    main()
