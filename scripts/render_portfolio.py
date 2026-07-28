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

# Badge images are hotlinked from TryHackMe's CDN (verified to serve HTTP 200).
BADGES_PER_ROW = 4
ROOMS_PER_ROW = 3

# Where a badge image links to.
#
# TryHackMe exposes per-badge pages at /<username>/badges/<slug>, and our
# badge "name" field is exactly that slug. Tempting - but visiting one in a
# logged-out browser redirected to the TryHackMe home page, so a reader
# clicking a badge would land on a marketing page rather than the badge.
# The profile URL is a destination that reliably works for a visitor who is
# not logged in, which is the only kind of visitor a public portfolio gets.
#
# To switch to per-badge deep links, return:
#   f"https://tryhackme.com/{username}/badges/{badge.get('name', '')}"
def badge_link(username: str, badge: dict) -> str:
    return f"https://tryhackme.com/p/{username}"


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


def build_stat_block(data: dict) -> list:
    """A centred row of headline figures: totals, then a count per tier.

    Rendered as an HTML table because Markdown cannot centre a block or lay
    cells out side by side. Only tiers that actually have rooms appear, so
    the row never carries a column of zeroes.
    """
    rooms = data.get("rooms") or []
    counts = Counter(r.get("difficulty", "") for r in rooms)

    cells = [
        ("Rooms Completed", str(data["rooms_completed"])),
        ("Badges Earned", str(data["badge_count"])),
    ]
    for difficulty in DIFFICULTY_ORDER:
        if counts.get(difficulty):
            emoji = DIFFICULTY_EMOJI.get(difficulty, "")
            cells.append((f"{emoji} {difficulty.title()}".strip(), str(counts[difficulty])))

    lines = ['<div align="center">', "", "<table>", "<tr>"]
    for label, value in cells:
        lines.append(
            f'<td align="center">&nbsp;<strong>{label}</strong>&nbsp;<br>{value}</td>'
        )
    lines += ["</tr>", "</table>", "", "</div>"]
    return lines


def room_link(room: dict) -> str:
    title = room.get("title", "Unknown room")
    code = room.get("code", "")
    return f"[{title}](https://tryhackme.com/room/{code})" if code else title


def room_link_html(room: dict) -> str:
    """Same link as room_link, but as HTML for use inside a grid cell."""
    title = room.get("title", "Unknown room")
    code = room.get("code", "")
    if not code:
        return title
    return f'<a href="https://tryhackme.com/room/{code}">{title}</a>'


def build_readme_section(data: dict) -> str:
    """Compact snapshot for the front page."""
    username = data["username"]
    rooms = data.get("rooms") or []
    badges = data.get("badges") or []

    lines = [
        f"**Profile:** [{username}](https://tryhackme.com/p/{username})  ",
        f"**Last synced:** {data['last_synced_utc']}",
        "",
    ]
    lines += build_stat_block(data)
    lines.append("")

    recent = badges[:RECENT_BADGE_COUNT]
    if recent:
        lines.append("**Recent badges:** " + " ".join(
            f"`{b.get('title', b.get('name', 'badge'))}`" for b in recent
        ))
        lines.append("")

    lines.append("Full room-by-room history and badge log: [TRAINING.md](TRAINING.md)")
    return "\n".join(lines)


def build_room_grids(lines: list, rooms: list) -> None:
    """Append difficulty-grouped room grids (hardest first) to `lines`.

    Rooms are laid out three across rather than as a single-column list: one
    column of names occupies about a quarter of GitHub's content width, so
    centring it strands a thin ribbon in whitespace and long sections scroll
    for over a page. Three across fills the measure and cuts the height.
    """
    by_difficulty = {}
    for room in rooms:
        by_difficulty.setdefault(room.get("difficulty", "") or "unspecified", []).append(room)

    # Known tiers hardest-first; any unfamiliar difficulty sorts to the end
    # rather than vanishing, so an API change adds a section, never drops one.
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
            '<div align="center">',
            "",
            "<table>",
        ]
        for row_start in range(0, len(group), ROOMS_PER_ROW):
            row = group[row_start:row_start + ROOMS_PER_ROW]
            lines.append("<tr>")
            for room in row:
                lines.append(f'<td align="left" width="300">{room_link_html(room)}</td>')
            # Pad the final row so the grid keeps square edges.
            for _ in range(ROOMS_PER_ROW - len(row)):
                lines.append('<td width="300"></td>')
            lines.append("</tr>")
        lines += ["</table>", "", "</div>"]


def build_training_section(data: dict) -> str:
    """The complete evidence log."""
    username = data["username"]
    rooms = data.get("rooms") or []
    badges = data.get("badges") or []

    lines = [
        f"**Profile:** [{username}](https://tryhackme.com/p/{username})  ",
        f"**Last synced:** {data['last_synced_utc']}",
        "",
    ]
    lines += build_stat_block(data)

    # Challenge rooms are solved unaided, so they lead - a reader sees them
    # before scrolling through the guided fundamentals. Anything that is not
    # a walkthrough counts as a challenge, so CTF/network types feature here
    # too rather than being lumped in with guided content.
    challenges = [r for r in rooms if r.get("type", "") != "walkthrough"]
    guided = [r for r in rooms if r.get("type", "") == "walkthrough"]

    if challenges and guided:
        # Both kinds present: split them so the type is conveyed by the
        # section, not by a label repeated under every single room.
        lines += ["", f"## Challenges ({len(challenges)})", "",
                  "_Solved without a guided walkthrough. Hardest first._"]
        build_room_grids(lines, challenges)
        lines += ["", f"## Guided Rooms ({len(guided)})", "",
                  "_Walkthrough rooms. Hardest first; related rooms grouped._"]
        build_room_grids(lines, guided)
    else:
        # Only one kind so far - a single flat section reads cleaner than a
        # near-empty "Challenges" heading beside everything else.
        lines += ["", f"## Completed rooms ({len(rooms)})", "",
                  "_Hardest first. Within each tier, related rooms are kept together._"]
        build_room_grids(lines, rooms)

    lines += ["", f"## Badges ({len(badges)})", ""]
    if not badges:
        lines.append("_No badges recorded yet._")
        return "\n".join(lines)

    # Rendered as an HTML table rather than a Markdown one because Markdown
    # has no way to lay images out in a grid. GitHub renders this subset of
    # HTML inside Markdown files.
    lines += ["<div align=\"center\">", "", "<table>"]
    for row_start in range(0, len(badges), BADGES_PER_ROW):
        row = badges[row_start:row_start + BADGES_PER_ROW]
        lines.append("<tr>")
        for badge in row:
            title = badge.get("title", badge.get("name", "badge"))
            image = badge.get("image", "")
            earned = format_date(badge.get("earnedAt", ""))
            tier = badge.get("rarityTier", "")
            percent = badge.get("rarityPercent")
            rarity = f"{tier} ({percent}%)" if tier and percent is not None else tier

            caption = " · ".join(part for part in (earned, rarity) if part)
            lines.append(f'<td align="center" width="130">')
            lines.append(f'<a href="{badge_link(username, badge)}">')
            if image:
                lines.append(f'<img src="{image}" alt="{title}" width="90"><br>')
            lines.append(f"<strong>{title}</strong>")
            lines.append("</a>")
            if caption:
                lines.append(f"<br><sub>{caption}</sub>")
            lines.append("</td>")
        lines.append("</tr>")
    lines += ["</table>", "", "</div>"]

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
