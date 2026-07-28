"""
fetch_thm.py

Pulls completed-room and badge data from TryHackMe's public profile
endpoints and saves it to data/thm_data.json.

These endpoints are the same ones your browser calls when you view a
public TryHackMe profile - they're not an officially documented/stable
API, so this script is written defensively: if a fetch fails for any
reason (TryHackMe changes something, times out, etc.), the previous
data file is left untouched rather than being wiped. Your portfolio
will show slightly stale data on a bad day, never a blank one.

Required environment variable:
    THM_USERNAME - your TryHackMe username (e.g. ouroboroswhite)
"""
import json
import os
import sys
from datetime import datetime, timezone

import requests

THM_USERNAME = os.environ.get("THM_USERNAME", "")

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DATA_PATH = os.path.join(BASE_DIR, "data", "thm_data.json")

HEADERS = {
    "User-Agent": f"portfolio-sync-bot (github.com/{THM_USERNAME or 'unknown'})"
}
TIMEOUT = 15


def fetch_paginated(endpoint: str, page_size: int = 100) -> list:
    """Page through a TryHackMe public-profile endpoint until it stops returning results."""
    docs = []
    page = 1
    while True:
        url = (
            f"https://tryhackme.com/api/v2/public-profile/{endpoint}"
            f"?username={THM_USERNAME}&limit={page_size}&page={page}"
        )
        resp = requests.get(url, headers=HEADERS, timeout=TIMEOUT)
        resp.raise_for_status()
        payload = resp.json()
        batch = payload.get("data", {}).get("docs", [])
        if not batch:
            break
        docs.extend(batch)
        if not payload.get("data", {}).get("hasNextPage"):
            break
        page += 1
    return docs


def load_existing():
    if os.path.exists(DATA_PATH):
        with open(DATA_PATH, "r", encoding="utf-8") as f:
            return json.load(f)
    return None


def save(data: dict) -> None:
    os.makedirs(os.path.dirname(DATA_PATH), exist_ok=True)
    with open(DATA_PATH, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2, ensure_ascii=False)


def main() -> None:
    if not THM_USERNAME:
        print(
            "THM_USERNAME must be set as an environment variable "
            "(your TryHackMe username, e.g. ouroboroswhite).",
            file=sys.stderr,
        )
        sys.exit(1)

    previous = load_existing()

    try:
        rooms = fetch_paginated("completed-rooms")
        badges = fetch_paginated("badges")
    except Exception as exc:  # noqa: BLE001 - deliberately broad: never crash the pipeline
        print(f"Fetch failed ({exc}); keeping previous data untouched.", file=sys.stderr)
        if previous is None:
            sys.exit(1)
        sys.exit(0)

    data = {
        "username": THM_USERNAME,
        "last_synced_utc": datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M UTC"),
        "rooms_completed": len(rooms),
        "rooms": rooms,
        "badges": sorted(badges, key=lambda b: b.get("earnedAt", ""), reverse=True),
        "badge_count": len(badges),
    }
    save(data)
    print(f"Synced {len(rooms)} rooms and {len(badges)} badges for {THM_USERNAME}.")


if __name__ == "__main__":
    main()
