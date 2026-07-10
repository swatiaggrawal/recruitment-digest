# Recruitment Digest

An unofficial, auto-updating mirror of the Employment News "All Jobs" listing
with a readable UI, a link to each department's site (where known), and a
"Find notification" search link for everything else.

## How it works

- `scraper/scrape.py` fetches the listing and writes `docs/data.json`.
- `.github/workflows/update.yml` runs that script once a day via GitHub
  Actions and commits the updated JSON.
- `docs/index.html` + `style.css` + `app.js` is a static page that reads
  `data.json` and renders it — search, sort, and "closing soon" filters
  included. GitHub Pages serves this folder directly, no server needed.

## Setup (10 minutes)

1. **Create a new GitHub repo** and push everything in this folder to it.
2. **Enable GitHub Pages**: repo → Settings → Pages → "Deploy from a branch"
   → branch `main`, folder `/docs` → Save. Your site will appear at
   `https://<your-username>.github.io/<repo-name>/`.
3. **Enable Actions**: repo → Settings → Actions → General → make sure
   "Allow all actions" is selected, and under Workflow permissions choose
   "Read and write permissions" (needed so the workflow can commit
   `data.json` back to the repo).
4. **Run it once manually**: repo → Actions tab → "Update job listings" →
   "Run workflow". Check that it completes and that `docs/data.json` in
   the repo now has real entries (not `"count": 0`).
5. After that it runs automatically every day at 03:00 UTC — edit the
   cron line in `update.yml` if you want it more/less often (e.g. weekly:
   `"0 3 * * 1"` for every Monday).

## If the scraper fails

Government site markup changes occasionally. The scraper finds the table
by matching header text ("ORGANISATION" + "POST") rather than a hardcoded
ID, so small markup tweaks shouldn't break it — but if the workflow run
fails, open the Actions log, find the printed error, and check
`find_jobs_table()` / `get_column_indexes()` in `scraper/scrape.py` against
the current page HTML.

## How department links get resolved

Instead of relying only on a hand-maintained list, the scraper resolves
each organisation's official site automatically, in this order:

1. **`scraper/org_cache.json`** — organisations already resolved on a
   previous run. This file is auto-generated and grows over time; the
   workflow commits it back to the repo after every run, so lookups only
   ever happen once per organisation.
2. **`scraper/org_mapping.json`** — a small curated substring-match list
   for common recurring organisations (SSC, UPSC, Railways, etc.), useful
   as a fast, guaranteed-correct override.
3. **Live search** — for anything not in either file, it searches
   `"<organisation>" official website` and prefers results on
   `.gov.in` / `.nic.in` / `.ac.in` / `.org.in` / `.res.in` / `.co.in`
   domains. Whatever it finds (or doesn't) gets cached, so this only
   costs time on an organisation's *first* appearance.

If a search comes back wrong for some organisation, just fix the URL
directly in `org_cache.json` (or add a proper entry to
`org_mapping.json`, which takes priority next time the cache is cleared)
— either way it'll stick from then on. Nothing found → the row just
shows the "Find notification" search button instead.

## Local testing

```bash
cd scraper
pip install -r requirements.txt
python scrape.py          # writes ../docs/data.json
cd ../docs
python -m http.server 8000
# open http://localhost:8000
```
