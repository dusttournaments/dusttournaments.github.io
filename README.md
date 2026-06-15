# DUST: Virtual Combat — Tournament Hub

A static GitHub Pages site that displays Challonge tournaments from the
community page:
https://challonge.com/communities/dustvirtualcombat/tournaments

## How it works

The community page is a JavaScript-rendered app, so a normal HTTP
request returns an empty shell. `fetch_tournaments.py` uses Playwright
(a headless browser) to load the page, wait for it to render, and
extract the tournament list into `tournaments.json`. No Challonge API
key is required.

## Setup

1. **Create a GitHub repo** (e.g. `dust-vc-tournaments`) and push all
   these files to it.

2. **Enable GitHub Pages**:
   - Go to the repo's Settings → Pages
   - Source: "Deploy from a branch"
   - Branch: `main`, folder: `/ (root)`
   - Your site will be live at `https://<your-username>.github.io/<repo-name>/`

3. **Run the workflow**:
   - The included GitHub Action (`.github/workflows/update.yml`) runs
     once a day and on manual trigger, regenerating `tournaments.json`
     and committing it.
   - Trigger it manually from the Actions tab ("Run workflow") to
     populate the data immediately after setup.

## Local testing

```bash
pip install playwright
python -m playwright install chromium
python fetch_tournaments.py
# then serve locally (fetch() requires http://, not file://):
python -m http.server 8000
```

## Files

- `index.html` — the site itself (search/filter UI, reads `tournaments.json`)
- `fetch_tournaments.py` — scrapes the Challonge community page via Playwright
- `tournaments.json` — generated data file consumed by the site
- `.github/workflows/update.yml` — scheduled job to keep data fresh

## Notes / limitations

- This relies on the current structure of Challonge's community page.
  If Challonge changes their site layout, the selectors in
  `fetch_tournaments.py` may need adjusting.
- Dates and participant counts are parsed from visible page text with
  regex, so formatting may not always be perfectly accurate — check
  `tournaments.json` after a run and adjust the parsing logic if needed.

