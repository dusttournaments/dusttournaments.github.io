#!/usr/bin/env python3
"""
fetch_tournaments.py

Fetches specific tournaments from the Challonge v1 API and writes them
to tournaments.json for use by index.html.

Usage:
    CHALLONGE_API_KEY=your_key_here python fetch_tournaments.py

Get an API key from: https://challonge.com/settings/developer

How it works:
- List the Challonge tournament URLs (the part after challonge.com/)
  for "DUST: Virtual Combat" tournaments in TOURNAMENT_URLS below.
- The script fetches each one via the v1 API and writes the combined
  result to tournaments.json.

You can find a tournament's URL slug from its Challonge page address,
e.g. for https://challonge.com/ProtocolDust8 the slug is "ProtocolDust8".

If a tournament is hosted under an organization subdomain
(<subdomain>.challonge.com/<url>), list it as "subdomain-url".
"""

import os
import json
import sys
import urllib.request
import urllib.parse
from datetime import datetime

API_BASE = "https://api.challonge.com/v1"
GAME_NAME = "DUST: Virtual Combat"

# Add the Challonge tournament URL slugs (the part after challonge.com/)
# for each "DUST: Virtual Combat" tournament you want listed.
# Example slugs: "ProtocolDust8", "ProtocolDust7", "myorg-Season1"
TOURNAMENT_URLS = [
    "ProtocolDust8",
]


def api_get(path, params=None):
    api_key = os.environ.get("CHALLONGE_API_KEY")
    if not api_key:
        sys.exit("Error: CHALLONGE_API_KEY environment variable not set.")

    params = params or {}
    params["api_key"] = api_key
    query = urllib.parse.urlencode(params)
    url = f"{API_BASE}{path}.json?{query}"

    req = urllib.request.Request(url, headers={"User-Agent": "dust-vc-tournament-site"})
    with urllib.request.urlopen(req) as resp:
        return json.loads(resp.read().decode())


def fetch_tournament(url_slug):
    try:
        data = api_get(f"/tournaments/{url_slug}")
        return data["tournament"]
    except Exception as e:
        print(f"Warning: could not fetch tournament '{url_slug}': {e}", file=sys.stderr)
        return None


def to_record(t):
    subdomain = t.get("subdomain")
    url_part = t.get("url")
    if subdomain:
        full_url = f"https://{subdomain}.challonge.com/{url_part}"
    else:
        full_url = f"https://challonge.com/{url_part}"

    return {
        "name": t.get("name"),
        "state": t.get("state"),
        "participants_count": t.get("participants_count"),
        "start_at": t.get("start_at"),
        "url": url_part,
        "full_challonge_url": full_url,
        "game_name": t.get("game_name") or GAME_NAME,
    }


def main():
    results = []
    seen_ids = set()

    for slug in TOURNAMENT_URLS:
        t = fetch_tournament(slug)
        if t and t["id"] not in seen_ids:
            results.append(to_record(t))
            seen_ids.add(t["id"])

    # Sort: in-progress first, then upcoming, then completed
    state_order = {"underway": 0, "pending": 1, "complete": 2}
    results.sort(key=lambda r: (state_order.get(r["state"], 3), r["start_at"] or ""))

    output = {
        "game": GAME_NAME,
        "last_updated": datetime.utcnow().isoformat() + "Z",
        "tournaments": results,
    }

    with open("tournaments.json", "w") as f:
        json.dump(output, f, indent=2)

    print(f"Wrote {len(results)} tournament(s) to tournaments.json")


if __name__ == "__main__":
    main()
