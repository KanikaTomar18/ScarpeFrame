"""
Tests for the selector/extraction logic.

Uses a mock fetcher backed by BeautifulSoup so these run fast and
without spinning up a real browser — only the parsing logic is under
test here, not Selenium itself.
"""

import sys
from pathlib import Path

from bs4 import BeautifulSoup

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from scraper import extract_items  # noqa: E402

FIXTURE_PATH = Path(__file__).parent / "fixtures" / "sample_page.html"


class MockElement:
    def __init__(self, tag):
        self.tag = tag

    @property
    def text(self):
        return self.tag.get_text()

    def get_attribute(self, name):
        return self.tag.get(name)


class MockFetcher:
    """Mimics the subset of SeleniumFetcher's interface extract_items needs."""

    def __init__(self, html: str):
        self.soup = BeautifulSoup(html, "html.parser")

    def find_elements(self, css_selector: str):
        return [MockElement(tag) for tag in self.soup.select(css_selector)]


def load_fetcher():
    html = FIXTURE_PATH.read_text(encoding="utf-8")
    return MockFetcher(html)


def test_extracts_titles_via_title_attribute():
    fetcher = load_fetcher()
    items = extract_items(fetcher, ["h3 a"], text_source="attr:title")
    assert items == ["A Light in the Attic", "Tipping the Velvet", "Soumission"]


def test_falls_back_to_text_when_no_attr_requested():
    fetcher = load_fetcher()
    items = extract_items(fetcher, ["h3 a"], text_source="text")
    assert items == ["A Light in...", "Tipping the...", "Soumission"]


def test_returns_empty_when_no_selector_matches():
    fetcher = load_fetcher()
    items = extract_items(fetcher, [".this-selector-matches-nothing"], text_source="text")
    assert items == []


def test_tries_selectors_in_order_until_one_matches():
    fetcher = load_fetcher()
    items = extract_items(
        fetcher,
        [".nonexistent-selector", "h3 a"],
        text_source="attr:title",
    )
    assert len(items) == 3
