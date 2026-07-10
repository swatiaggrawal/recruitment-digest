#!/usr/bin/env python3
"""
Scrapes the "All Jobs" listing from employmentnews.gov.in and writes a
structured JSON file (docs/data.json) that the frontend reads.

The site itself does not link to individual job postings, so for every
row we generate:
  - a "department_url": resolved automatically in this order -
      1) scraper/org_cache.json - orgs already resolved on a past run
      2) scraper/org_mapping.json - a small curated list of known orgs
      3) a live search (DuckDuckGo HTML results) for "<org> official website",
         preferring .gov.in/.nic.in/.ac.in/etc domains - the result is then
         written into org_cache.json so it's never searched again
  - a "search_url": a Google search targeted at the org + post, which
    reliably surfaces the actual notification/PDF

Run:
    python scrape.py
"""

import json
import re
import sys
import time
import hashlib
from datetime import datetime, timezone
from pathlib import Path
from urllib.parse import quote_plus, urlparse, parse_qs, unquote

import requests
from bs4 import BeautifulSoup

SOURCE_URL = "https://employmentnews.gov.in/NewEmp/AllJobs.aspx?k=All"
ROOT = Path(__file__).resolve().parent.parent
ORG_MAP_PATH = Path(__file__).resolve().parent / "org_mapping.json"
ORG_CACHE_PATH = Path(__file__).resolve().parent / "org_cache.json"
OUTPUT_PATH = ROOT / "docs" / "data.json"

HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
        "(KHTML, like Gecko) Chrome/124.0 Safari/537.36"
    )
}

# Domains that look like a genuine official/government site, checked in
# priority order when picking among search results.
PREFERRED_SUFFIXES = (".gov.in", ".nic.in", ".ac.in", ".org.in", ".res.in", ".co.in")


def load_json(path):
    if path.exists():
        with open(path, "r", encoding="utf-8") as f:
            return json.load(f)
    return {}


def save_json(path, data):
    with open(path, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2, sort_keys=True)


def find_department_url_curated(org_name, org_mapping):
    org_upper = org_name.upper()
    for key, url in org_mapping.items():
        if key == "_comment":
            continue
        if key.upper() in org_upper:
            return url
    return None


def extract_redirect_target(href):
    """DuckDuckGo's HTML results wrap outbound links in a redirect URL
    like //duckduckgo.com/l/?uddg=<encoded-real-url>&rut=...
    Pull the real target out of it; pass through plain http(s) links as-is.
    """
    if href.startswith("//"):
        href = "https:" + href
    if "duckduckgo.com/l/" in href:
        qs = parse_qs(urlparse(href).query)
        target = qs.get("uddg", [None])[0]
        return unquote(target) if target else None
    if href.startswith("http"):
        return href
    return None


def guess_department_url(org_name):
    """Live web search fallback for organisations not in the curated
    mapping or cache yet. Returns None on any failure rather than raising,
    since this should never block the rest of the scrape.
    """
    query = f'"{org_name}" official website'
    url = "https://html.duckduckgo.com/html/?q=" + quote_plus(query)
    try:
        resp = requests.get(url, headers=HEADERS, timeout=15)
        resp.raise_for_status()
    except Exception as e:
        print(f"  search failed for '{org_name}': {e}", file=sys.stderr)
        return None

    soup = BeautifulSoup(resp.text, "html.parser")
    candidates = []
    for a in soup.select("a.result__a"):
        target = extract_redirect_target(a.get("href", ""))
        if target:
            candidates.append(target)

    if not candidates:
        return None

    for u in candidates:
        domain = urlparse(u).netloc.lower()
        if any(domain.endswith(suf) for suf in PREFERRED_SUFFIXES):
            return u

    # No obviously-official domain found; use the top result as a best guess.
    return candidates[0]


def resolve_department_url(org_name, org_mapping, org_cache):
    """Lookup order: auto-learned cache -> curated mapping -> live search
    (which then gets written into the cache for next time)."""
    if org_name in org_cache:
        return org_cache[org_name]

    curated = find_department_url_curated(org_name, org_mapping)
    if curated:
        org_cache[org_name] = curated
        return curated

    guessed = guess_department_url(org_name)
    time.sleep(1)  # be polite to the search endpoint between lookups
    org_cache[org_name] = guessed  # cache the miss too, so we don't re-search every day
    return guessed


def build_search_url(org, post):
    query = f'"{org.strip()}" "{post.strip()}" recruitment notification pdf'
    return "https://www.google.com/search?q=" + quote_plus(query)


def make_job_id(issued_date, org, post):
    raw = f"{issued_date}|{org}|{post}".lower().strip()
    return hashlib.sha1(raw.encode("utf-8")).hexdigest()[:12]


def find_jobs_table(soup):
    for table in soup.find_all("table"):
        header_row = table.find("tr")
        if not header_row:
            continue
        header_text = header_row.get_text(" ", strip=True).upper()
        if "ORGANISATION" in header_text and "POST" in header_text:
            return table
    return None


def get_column_indexes(header_cells):
    org_idx = post_idx = issued_idx = method_idx = last_idx = -1
    for i, cell in enumerate(header_cells):
        text = cell.get_text(strip=True).upper()
        if "ORGANISATION" in text:
            org_idx = i
        elif text == "POST" or ("POST" in text and "METHOD" not in text):
            post_idx = i
        elif "ISSUED" in text:
            issued_idx = i
        elif "METHOD" in text:
            method_idx = i
        elif "LAST" in text:
            last_idx = i
    return issued_idx, org_idx, post_idx, method_idx, last_idx


def scrape():
    resp = requests.get(SOURCE_URL, headers=HEADERS, timeout=30)
    resp.raise_for_status()
    soup = BeautifulSoup(resp.text, "html.parser")

    table = find_jobs_table(soup)
    if table is None:
        raise RuntimeError(
            "Could not find the jobs table on the page. "
            "The site's markup may have changed - inspect the HTML and "
            "update find_jobs_table()/get_column_indexes()."
        )

    rows = table.find_all("tr")
    header_cells = rows[0].find_all(["th", "td"])
    issued_idx, org_idx, post_idx, method_idx, last_idx = get_column_indexes(header_cells)

    if org_idx == -1 or post_idx == -1:
        raise RuntimeError("Could not locate ORGANISATION/POST columns.")

    org_mapping = load_json(ORG_MAP_PATH)
    org_cache = load_json(ORG_CACHE_PATH)
    jobs = []

    for row in rows[1:]:
        cells = row.find_all("td")
        if not cells or len(cells) <= max(org_idx, post_idx):
            continue

        def cell_text(idx):
            return cells[idx].get_text(" ", strip=True) if 0 <= idx < len(cells) else ""

        org = cell_text(org_idx)
        post = cell_text(post_idx)
        if not org and not post:
            continue

        issued_date = cell_text(issued_idx)
        method = cell_text(method_idx)
        last_date = cell_text(last_idx)

        jobs.append({
            "id": make_job_id(issued_date, org, post),
            "issued_date": issued_date,
            "organisation": org,
            "post": post,
            "appointment_method": method,
            "last_date": last_date,
            "department_url": resolve_department_url(org, org_mapping, org_cache),
            "search_url": build_search_url(org, post),
        })

    save_json(ORG_CACHE_PATH, org_cache)
    return jobs


def main():
    try:
        jobs = scrape()
    except Exception as e:
        print(f"ERROR: scrape failed: {e}", file=sys.stderr)
        sys.exit(1)

    if not jobs:
        print("WARNING: no jobs parsed - not overwriting existing data.json", file=sys.stderr)
        sys.exit(1)

    output = {
        "last_updated": datetime.now(timezone.utc).isoformat(),
        "source_url": SOURCE_URL,
        "count": len(jobs),
        "jobs": jobs,
    }

    OUTPUT_PATH.parent.mkdir(parents=True, exist_ok=True)
    with open(OUTPUT_PATH, "w", encoding="utf-8") as f:
        json.dump(output, f, ensure_ascii=False, indent=2)

    print(f"Wrote {len(jobs)} jobs to {OUTPUT_PATH}")


if __name__ == "__main__":
    main()
