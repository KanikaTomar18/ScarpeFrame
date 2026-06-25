"""
Generic directory/listing scraper.

Takes a YAML config describing a target site's selectors and pagination
style, and scrapes listing text into a CSV. Selectors, URLs, and pacing
all live in config — no code changes needed to point this at a new site.

Designed for sites that need a real browser (JS-rendered listings).
For static HTML, swap SeleniumFetcher for a requests+BeautifulSoup
fetcher behind the same interface.
"""

import csv
import json
import logging
import random
import time
from pathlib import Path

import yaml

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger(__name__)


class ScraperConfig:
    """Loads and validates a site config from YAML."""

    def __init__(self, path: str):
        with open(path, "r", encoding="utf-8") as f:
            raw = yaml.safe_load(f)

        self.site_name = raw["site_name"]
        self.base_url = raw["base_url"]
        self.start_page = raw.get("start_page", 1)
        self.max_pages = raw.get("max_pages", 5)
        self.item_selectors = raw["item_selectors"]
        self.text_source = raw.get("text_source", "text")
        self.pagination_type = raw.get("pagination", {}).get("type", "url_pattern")
        delay = raw.get("request_delay_seconds", [2, 4])
        self.delay_min, self.delay_max = delay[0], delay[1]
        self.headless = raw.get("headless", True)
        self.output_file = raw.get("output_file", "scraped_output.csv")
        self.checkpoint_file = raw.get("checkpoint_file", "checkpoint.json")


class Checkpoint:
    """Tracks progress so a crashed/interrupted run can resume."""

    def __init__(self, path: str):
        self.path = Path(path)
        self.last_completed_page = 0
        self.collected = []
        if self.path.exists():
            data = json.loads(self.path.read_text(encoding="utf-8"))
            self.last_completed_page = data.get("last_completed_page", 0)
            self.collected = data.get("collected", [])
            logger.info(
                "Resuming from checkpoint: page %s, %s items already collected",
                self.last_completed_page,
                len(self.collected),
            )

    def save(self, page_num: int, collected: list):
        self.last_completed_page = page_num
        self.collected = collected
        self.path.write_text(
            json.dumps(
                {"last_completed_page": page_num, "collected": collected},
                ensure_ascii=False,
            ),
            encoding="utf-8",
        )

    def clear(self):
        if self.path.exists():
            self.path.unlink()


class SeleniumFetcher:
    """Thin wrapper around a Selenium Chrome driver."""

    def __init__(self, headless: bool = True):
        # Imported lazily so unit-testing extract_items() doesn't require
        # selenium/chromedriver to be installed.
        from selenium import webdriver
        from selenium.webdriver.chrome.options import Options
        from selenium.webdriver.chrome.service import Service
        from selenium.webdriver.support.ui import WebDriverWait
        from webdriver_manager.chrome import ChromeDriverManager

        options = Options()
        options.add_argument("--disable-dev-shm-usage")
        options.add_argument("--no-sandbox")
        options.add_argument("--disable-gpu")
        options.add_argument("--window-size=1920,1080")
        options.add_argument(
            "--user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
            "AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
        )
        if headless:
            options.add_argument("--headless=new")

        service = Service(ChromeDriverManager().install())
        self.driver = webdriver.Chrome(service=service, options=options)
        self.wait = WebDriverWait(self.driver, 20)

    def get(self, url: str):
        self.driver.get(url)

    def find_elements(self, css_selector: str):
        from selenium.webdriver.common.by import By

        return self.driver.find_elements(By.CSS_SELECTOR, css_selector)

    def quit(self):
        self.driver.quit()


def extract_items(fetcher, selectors: list, text_source: str) -> list:
    """Try each selector in order; use the first one that returns results."""
    for selector in selectors:
        elements = fetcher.find_elements(selector)
        if not elements:
            continue
        logger.info("Matched %s items with selector: %s", len(elements), selector)
        items = []
        for el in elements:
            try:
                if text_source.startswith("attr:"):
                    attr_name = text_source.split(":", 1)[1]
                    value = el.get_attribute(attr_name)
                else:
                    value = el.text
                value = (value or "").strip()
                if value and len(value) > 2:
                    items.append(value)
            except Exception as e:
                logger.debug("Skipping element due to error: %s", e)
        return items
    return []


def save_to_csv(items: list, filename: str):
    with open(filename, "w", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        writer.writerow(["Item"])
        for item in items:
            writer.writerow([item])
    logger.info("Saved %s items to %s", len(items), filename)


def run(config: ScraperConfig, resume: bool = True):
    checkpoint = Checkpoint(config.checkpoint_file) if resume else Checkpoint(
        config.checkpoint_file
    )
    if not resume:
        checkpoint.clear()
        checkpoint = Checkpoint(config.checkpoint_file)

    all_items = list(checkpoint.collected)
    start_page = max(config.start_page, checkpoint.last_completed_page + 1)

    fetcher = SeleniumFetcher(headless=config.headless)
    try:
        for page_num in range(start_page, config.start_page + config.max_pages):
            url = config.base_url.format(page=page_num)
            logger.info("Fetching page %s: %s", page_num, url)

            try:
                fetcher.get(url)
            except Exception as e:
                logger.error("Failed to load page %s: %s", page_num, e)
                break  # stop, but keep what we have via checkpoint

            time.sleep(random.uniform(config.delay_min, config.delay_max))

            page_items = extract_items(fetcher, config.item_selectors, config.text_source)
            if not page_items:
                logger.info("No items found on page %s — assuming end of results", page_num)
                break

            all_items.extend(page_items)
            checkpoint.save(page_num, list(dict.fromkeys(all_items)))
            logger.info(
                "Page %s done: +%s items (total so far: %s)",
                page_num,
                len(page_items),
                len(all_items),
            )

    finally:
        fetcher.quit()

    unique_items = list(dict.fromkeys(all_items))
    save_to_csv(unique_items, config.output_file)
    checkpoint.clear()  # successful full run — no need to resume further
    return unique_items
