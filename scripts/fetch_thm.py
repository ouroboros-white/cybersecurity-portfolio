"""
fetch_thm.py

Pulls completed-room and badge data from TryHackMe's public profile
endpoints and saves it to data/thm_data.json.

These endpoints are the same ones your browser calls when you view a
public TryHackMe profile - they're not an officially documented/stable
API, so this script is written defensively:
  - if a request is rate-limited (HTTP 429) or hits a server error (5xx),
    it waits briefly and retries a few times before giving up
  - if it still fails after retrying, the previous data file is left
    untouched rather than being wiped, so a bad sync never blanks your
    portfolio - it just skips that update and logs a warning

Required environment variable:
    THM_USERNAME - your TryHackMe username (e.g. ouroboroswhite)
"""
import json
import os
import sys
import time
from datetime import datetime, timezone

import requests

THM_USERNAME = os.environ.get("THM_USERNAME", "")

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DATA_PATH = os.path.join(BASE_DIR, "data", "thm_data.json")

HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
        "(KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36"
    ),
    "Accept": "application/json",
}
TIMEOUT = 15

# Retry settings: how many attempts, and how long to wait between them.
# The wait time doubles each attempt (1s, 2s, 4s...) so we back off
# instead of hammering a server that's already asking us to slow down.
MAX_ATTEMPTS = 4
INITIAL_BACKOFF_SECONDS = 2


def get_with_retries(url: str) -> dict:
    """GET a URL, retrying on rate limits (429) and server errors (5xx)."""
    last_error = None
    for attempt in range(1, MAX_ATTEMPTS + 1):
        try:
            resp = requests.get(url, headers=HEADERS, timeout=TIMEOUT)
            if resp.status_code == 429 or resp.status_code >= 500:
                last_error = f"HTTP {resp.status_code} from {url}"
                if attempt < MAX_ATTEMPTS:
                    wait = INITIAL_BACKOFF_SECONDS * (2 ** (attempt - 1))
                    print(
                        f"  Attempt {attempt} got {resp.status_code}; "
                        f"waiting {wait}s before retrying...",
                        file=sys.stderr,
                    )
                    time.sleep(wait)
                    continue
                resp.raise_for_status()
            resp.raise_for_status()
            return resp.json()
        except requests.RequestException as exc:
            last_error = str(exc)
            if attempt < MAX_ATTEMPTS:
                wait = INITIAL_BACKOFF_SECONDS * (2 ** (attempt - 1))
                print(
                    f"  Attempt {attempt} failed ({exc}); "
                    f"waiting {wait}s before retrying...",
                    file=sys.stderr,
                )
                time.sleep(wait)
    raise RuntimeError(f"Giving up after {MAX_ATTEMPTS} attempts: {last_error}")


def fetch_paginated(endpoint: str, page_size: int = 100) -> list:
    """Page through a TryHackMe public-profile endpoint until it stops returning results."""
    docs = []
    page = 1
    while True:
        url = (
            f"https://tryhackme.com/api/v2/public-profile/{endpoint}"
            f"?username={THM_USERNAME}&limit={page_size}&page={page}"
        )
        payload = get_with_retries(url)
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
        print("Fetching completed rooms...")
        rooms = fetch_paginated("completed-rooms")
        print("Fetching badges...")
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