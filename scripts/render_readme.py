"""
render_readme.py

Fills in the auto-generated section of README.md (everything between
the <!--THM:START--> and <!--THM:END--> markers) using
data/thm_data.json. Everything outside those markers - your own bio,
project write-ups, contact links, etc. - is left exactly as you wrote
it, every time this runs.
"""
import json
import os
import re

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DATA_PATH = os.path.join(BASE_DIR, "data", "thm_data.json")
README_PATH = os.path.join(BASE_DIR, "README.md")

START = "<!--THM:START-->"
END = "<!--THM:END-->"

DIFFICULTY_EMOJI = {"info": "ℹ️", "easy": "🟢", "medium": "🟡", "hard": "🔴", "insane": "⚫"}


def build_section(data: dict) -> str:
    lines = []
    username = data["username"]
    lines.append(f"**Profile:** [{username}](https://tryhackme.com/p/{username})  ")
    lines.append(f"**Last synced:** {data['last_synced_utc']}")
    lines.append("")
    lines.append("| Rooms completed | Badges earned |")
    lines.append("|---|---|")
    lines.append(f"| {data['rooms_completed']} | {data['badge_count']} |")
    lines.append("")
    lines.append("### Completed rooms")
    lines.append("")
    lines.append("| Room | Difficulty |")
    lines.append("|---|---|")
    for room in data["rooms"]:
        title = room.get("title", "Unknown room")
        code = room.get("code", "")
        difficulty = room.get("difficulty", "")
        emoji = DIFFICULTY_EMOJI.get(difficulty, "")
        link = f"[{title}](https://tryhackme.com/room/{code})" if code else title
        lines.append(f"| {link} | {emoji} {difficulty} |")
    lines.append("")
    lines.append("### Badges")
    lines.append("")
    badges = data.get("badges") or []
    if badges:
        badge_text = " ".join(f"`{b.get('title', b.get('name', 'badge'))}`" for b in badges)
    else:
        badge_text = "_No badges recorded yet._"
    lines.append(badge_text)
    return "\n".join(lines)


def main() -> None:
    with open(DATA_PATH, "r", encoding="utf-8") as f:
        data = json.load(f)
    with open(README_PATH, "r", encoding="utf-8") as f:
        readme = f.read()

    if START not in readme or END not in readme:
        raise SystemExit(
            "README.md is missing the <!--THM:START--> / <!--THM:END--> "
            "markers. Add them at the point where the auto-generated "
            "section should appear, then re-run."
        )

    section = build_section(data)
    pattern = re.compile(re.escape(START) + r".*?" + re.escape(END), re.DOTALL)
    new_readme = pattern.sub(f"{START}\n{section}\n{END}", readme)

    with open(README_PATH, "w", encoding="utf-8") as f:
        f.write(new_readme)

    print("README.md updated.")


if __name__ == "__main__":
    main()
