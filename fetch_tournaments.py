#!/usr/bin/env python3
"""
fetch_tournaments.py

Scrapes the Challonge community page for "DUST: Virtual Combat"
(https://challonge.com/communities/dustvirtualcombat/tournaments)
and writes the resulting tournament list to tournaments.json for use
by index.html.

The community page is a JavaScript-rendered single-page app, so this
script uses Playwright (a headless browser) to load the page, wait for
the tournament list to render, and then extract the data from the DOM.

Usage:
    python fetch_tournaments.py

Setup (first time):
    pip install playwright
    python -m playwright install chromium

Run this on a schedule (e.g. via GitHub Actions) to keep
tournaments.json up to date.
"""

import json
import re
import sys
from datetime import datetime

from playwright.sync_api import sync_playwright

COMMUNITY_URL = "https://challonge.com/communities/dustvirtualcombat/tournaments"
GAME_NAME = "DUST: Virtual Combat"


def scrape():
    results = []

    with sync_playwright() as p:
        browser = p.chromium.launch()
        page = browser.new_page()

        try:
            page.goto(COMMUNITY_URL, wait_until="domcontentloaded", timeout=60000)
        except Exception as e:
            print(f"Warning: page.goto issue: {e}", file=sys.stderr)

        # Give the SPA time to render its content
        page.wait_for_timeout(8000)

        # Wait for tournament cards/links to appear. Challonge tournament
        # links point at <subdomain>.challonge.com/<url> or challonge.com/<url>.
        try:
            page.wait_for_selector("a[href*='challonge.com']", timeout=30000)
        except Exception:
            print("Warning: no tournament links appeared within timeout.", file=sys.stderr)

        # Grab every tournament card. Challonge renders each tournament as a
        # link wrapping (or near) a title, status badge, date, and
        # participant count. We collect anchors and pull nearby text.
        cards = page.eval_on_selector_all(
            "a[href*='challonge.com']",
            """
            (els) => els.map(el => {
                const container = el.closest('[class*="card"], [class*="Card"], li, div') || el;
                return {
                    href: el.href,
                    text: container.innerText || ''
                };
            })
            """
        )

        browser.close()

    seen_urls = set()
    for card in cards:
        href = card["href"]
        text = card["text"].strip()

        # Skip non-tournament links (nav, footer, etc.)
        if "/communities/" in href or "challonge.com" == href.rstrip("/").split("//")[-1]:
            continue
        if href in seen_urls:
            continue
        if not text:
            continue

        seen_urls.add(href)

        lines = [l.strip() for l in text.split("\n") if l.strip()]
        name = lines[0] if lines else href

        state = "unknown"
        lower_text = text.lower()
        if "complete" in lower_text or "finished" in lower_text:
            state = "complete"
        elif "underway" in lower_text or "in progress" in lower_text or "live" in lower_text:
            state = "underway"
        elif "pending" in lower_text or "upcoming" in lower_text or "registration" in lower_text:
            state = "pending"

        participants_match = re.search(r"(\d+)\s*(participants?|players?|entrants?)", lower_text)
        participants_count = int(participants_match.group(1)) if participants_match else None

        # Try to find a date-like string
        start_at = None
        date_match = re.search(
            r"\b(Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec)[a-z]*\.?\s+\d{1,2}(,?\s+\d{4})?\b",
            text
        )
        if date_match:
            start_at = date_match.group(0)

        results.append({
            "name": name,
            "state": state,
            "participants_count": participants_count,
            "start_at": start_at,
            "url": href.split("/")[-1],
            "full_challonge_url": href,
            "game_name": GAME_NAME,
        })

    return results


def main():
    results = scrape()

    state_order = {"underway": 0, "pending": 1, "complete": 2, "unknown": 3}
    results.sort(key=lambda r: state_order.get(r["state"], 3))

    output = {
        "game": GAME_NAME,
        "source": COMMUNITY_URL,
        "last_updated": datetime.utcnow().isoformat() + "Z",
        "tournaments": results,
    }

    with open("tournaments.json", "w") as f:
        json.dump(output, f, indent=2)

    print(f"Wrote {len(results)} tournament(s) to tournaments.json")


if __name__ == "__main__":
    main()
