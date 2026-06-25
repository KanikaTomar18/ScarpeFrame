# Generic Directory Scraper

A configuration-driven web scraper for extracting listing data (companies,
products, articles — anything paginated) from directory-style websites.
Built originally for a freelance client project, scraping a business
directory; generalized here so the core engine isn't tied to any one site.

The demo config in this repo points at [books.toscrape.com](https://books.toscrape.com),
a site built specifically for practicing scrapers, so anyone can clone this
and see it run end-to-end without scraping a real company's data.

## Key Highlights

- Config-driven scraper architecture
- YAML-based site configuration
- Checkpoint and resume support
- CLI interface with runtime overrides
- Unit-tested extraction layer
- CSV export pipeline


## Why this exists

The original version of this scraper was hardcoded to one site: the target
URL, CSS selectors, and pagination logic were all baked into the script.
That's fine for a one-off job, but it meant the actual reusable part — page
fetching, selector fallback, retry/resume logic — was tangled up with
site-specific details.

This version separates the two:

- **Config (YAML)** — what to scrape: base URL, selectors, pagination style, pacing
- **Engine (Python)** — how to scrape: fetch pages, try selectors in order,
  checkpoint progress, write CSV

Pointing this at a new site means writing a new config file, not new code.

## Features

- **Selector fallback chain** — tries a list of CSS selectors per page and
  uses the first one that returns results, so minor markup differences
  across pages don't break the whole run.
- **Checkpointing** — progress is saved after every page to a JSON
  checkpoint file. If the process crashes or is killed on page 340 of 2,000,
  re-running picks up from page 341 instead of starting over.
- **CLI, not `input()`** — run unattended, in a cron job, or in CI. Flags
  override config values for quick one-off tests (`--max-pages 2`).
- **Polite by default** — randomized delay between page loads, configurable
  per site.
- **Tested extraction logic** — the selector/parsing logic is covered by
  unit tests against a static HTML fixture, independent of Selenium, so the
  parsing behavior can be verified without spinning up a browser.

## Project structure

```
generic-directory-scraper/
├── scraper.py              # Core engine: config loading, fetching, extraction, checkpointing
├── cli.py                  # Command-line entry point
├── config.example.yaml     # Demo config (books.toscrape.com)
├── requirements.txt
└── tests/
    ├── test_extraction.py
    └── fixtures/sample_page.html
```

## Tech Stack

- Python
- Selenium
- BeautifulSoup4
- PyYAML
- Pytest
- CSV
- JSON

## Usage

```bash
pip install -r requirements.txt

# Run the demo scrape (5 pages of books.toscrape.com)
python cli.py --config config.example.yaml

# Quick test run, visible browser
python cli.py --config config.example.yaml --max-pages 2 --no-headless

# Ignore any saved checkpoint and start fresh
python cli.py --config config.example.yaml --fresh
```

Output is written to the CSV path set in the config (`scraped_books.csv`
in the demo).

## Pointing this at a different site

Copy `config.example.yaml`, then update:

- `base_url` — must include `{page}` if using `pagination.type: url_pattern`
- `item_selectors` — CSS selectors for the listing items, in priority order
- `text_source` — `text` to read the element's text, or `attr: NAME` to read
  an HTML attribute (e.g., `attr: title`)
- `request_delay_seconds` — be considerate; check the target site's
  `robots.txt` and the terms of service before scraping it

No code changes needed for sites with the same general "paginated listing"
shape.

## Running the tests

```bash
pip install pytest beautifulsoup4
python -m pytest tests/ -v
```

The tests run against a static HTML fixture and don't require Chrome or
network access.

## Notes on responsible scraping

This tool includes pacing controls and checkpointing so that scraping runs
are predictable and don't hammer a target server. Before pointing it at any
site, check that site's `robots.txt` and terms of service, and prefer an
official API where one is available.

## Background

This project originated from a freelance scraping requirement involving a business directory. After completing the initial solution, the scraper was refactored into a reusable, configuration-driven framework with support for checkpointing, selector fallbacks, CLI execution, and automated testing.

## Demo
<img width="1438" height="792" alt="image" src="https://github.com/user-attachments/assets/5c8fdb20-4eda-4aad-8576-8df9ce55cc74" />
<img width="1448" height="327" alt="image" src="https://github.com/user-attachments/assets/a4788e10-60aa-4dbd-a23f-eaf37be71acb" />
<img width="1443" height="598" alt="image" src="https://github.com/user-attachments/assets/13eaa714-9cdf-408c-a811-cd2f85026405" />
* First, the command for running the project
* Second, for the visible browser
* Third, for saving the unique checkpoints



