# Recruitment Digest

A cleaner, self-updating mirror of the Government of India's [Employment
News](https://employmentnews.gov.in/NewEmp/AllJobs.aspx?k=All) job listings —
searchable, sortable, and with an actual link to follow for every posting.

The official site lists jobs in a plain table with no way to search, sort,
or click through to the actual notification. This project scrapes that
table daily, figures out where each posting actually leads, and serves it
as a proper page.

## What it does

- **Refreshes automatically** — a GitHub Actions workflow re-scrapes the
  listing once a day and commits the update, no server required.
- **Links you somewhere useful** — every listing gets a link to the
  hiring department's official site (resolved automatically, see below),
  plus a targeted search link that surfaces the actual notification PDF.
- **Surfaces what matters** — sort by closing date, filter to "closing
  soon," and search by organisation or post, instead of scrolling a huge
  static table.

## How it's built

```
scraper/scrape.py   →   docs/data.json   →   docs/index.html (+ style.css, app.js)
     ↑                                              ↑
runs daily via                                 static page,
GitHub Actions                                 served by GitHub Pages
```

- **`scraper/scrape.py`** fetches the listing, parses each row (organisation,
  post, dates, appointment method), and resolves a department link and a
  search link for it.
- **`docs/`** is a plain HTML/CSS/JS page — no build step, no framework —
  that reads `data.json` and renders it.
- **`.github/workflows/update.yml`** runs the scraper on a schedule and
  pushes the refreshed data back to the repo.

### How department links get resolved

Each organisation's official site is found automatically, checked in
this order, cheapest first:

1. **`scraper/org_cache.json`** — anything already resolved on a previous
   run. Auto-generated, grows over time, committed back by the workflow —
   so a given organisation is only ever looked up once.
2. **`scraper/org_mapping.json`** — a small curated list for common,
   recurring organisations (SSC, UPSC, Railways, etc.), which always wins
   as a guaranteed-correct override.
3. **Live search** — for anything new, it searches
   `"<organisation>" official website` and prefers `.gov.in` / `.nic.in`
   / `.ac.in` / `.org.in` / `.res.in` / `.co.in` domains. Whatever it
   finds gets written into the cache, so it's a one-time cost per
   organisation.

If nothing suitable turns up, the listing still gets a "Find
notification" search button as a fallback.

## Running it locally

```bash
cd scraper
pip install -r requirements.txt
python scrape.py            # writes ../docs/data.json

cd ../docs
python -m http.server 8000  # open http://localhost:8000
```

## If a listing looks wrong

- **Scraper stops finding rows at all** — the site's markup probably
  changed. `find_jobs_table()` and `get_column_indexes()` in
  `scraper/scrape.py` locate columns by header text rather than a fixed
  ID, so small changes shouldn't break it, but check the Actions log for
  the printed error if a run fails.
- **A department link is wrong for one organisation** — edit the entry
  directly in `scraper/org_cache.json` (or add a proper override to
  `scraper/org_mapping.json`, which always takes priority) — it'll stick
  from then on.

## Disclaimer

This is an independent, unofficial project. Data is sourced from
[Employment News](https://employmentnews.gov.in/NewEmp/AllJobs.aspx?k=All);
always verify details against the original notification before applying.
