"""
Google Maps business scraper wrapper.
Uses gosom/google-maps-scraper (MIT license) Go binary via subprocess.
"""

import csv
import io
import os
import subprocess
import tempfile
from dataclasses import dataclass, field


SCRAPER_BINARY = os.environ.get("GMAPS_SCRAPER_BIN", "/usr/local/bin/google-maps-scraper")
DEFAULT_TIMEOUT = int(os.environ.get("GMAPS_SCRAPER_TIMEOUT", "300"))


@dataclass
class ScrapedBusiness:
    name: str = ""
    category: str = ""
    address: str = ""
    phone: str = ""
    website: str = ""
    rating: float = 0.0
    review_count: int = 0
    latitude: float = 0.0
    longitude: float = 0.0
    status: str = ""
    raw: dict = field(default_factory=dict)


def scrape_google_maps(query: str, timeout: int = DEFAULT_TIMEOUT) -> list[ScrapedBusiness]:
    """
    Run the Google Maps scraper binary with a search query.
    Returns list of ScrapedBusiness objects.
    """
    if not os.path.isfile(SCRAPER_BINARY):
        raise FileNotFoundError(
            f"Scraper binary not found at {SCRAPER_BINARY}. "
            "Build it with: go install github.com/gosom/google-maps-scraper@latest"
        )

    with tempfile.TemporaryDirectory(prefix="gmaps_") as tmpdir:
        input_file = os.path.join(tmpdir, "input.txt")
        output_file = os.path.join(tmpdir, "results.csv")

        with open(input_file, "w") as f:
            f.write(query.strip() + "\n")

        cmd = [
            SCRAPER_BINARY,
            "-input", input_file,
            "-results", output_file,
            "-exit-on-inactivity", "30s",
        ]

        try:
            subprocess.run(
                cmd,
                timeout=timeout,
                capture_output=True,
                text=True,
            )
        except subprocess.TimeoutExpired:
            pass  # scraper may still have written partial results

        if not os.path.isfile(output_file):
            return []

        return _parse_csv(output_file)


def _parse_csv(filepath: str) -> list[ScrapedBusiness]:
    """Parse scraper CSV output into ScrapedBusiness objects."""
    results = []
    with open(filepath, "r", encoding="utf-8", errors="replace") as f:
        reader = csv.DictReader(f)
        for row in reader:
            biz = ScrapedBusiness(
                name=row.get("title", "").strip(),
                category=row.get("category", "").strip(),
                address=row.get("address", "").strip(),
                phone=row.get("phone", "").strip(),
                website=row.get("web_site", row.get("website", "")).strip(),
                rating=_safe_float(row.get("rating", "0")),
                review_count=_safe_int(row.get("reviews", "0")),
                latitude=_safe_float(row.get("latitude", "0")),
                longitude=_safe_float(row.get("longitude", "0")),
                status=row.get("status", "").strip(),
                raw=dict(row),
            )
            if biz.name:
                results.append(biz)
    return results


def _safe_float(val: str) -> float:
    try:
        return float(val)
    except (ValueError, TypeError):
        return 0.0


def _safe_int(val: str) -> int:
    try:
        return int(float(val))
    except (ValueError, TypeError):
        return 0
