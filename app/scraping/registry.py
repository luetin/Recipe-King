from urllib.parse import urlparse

import httpx

from app.scraping.base import ScrapeError, ScraperResult
from app.scraping.jsonld import JsonLdScraper
from app.scraping.sites.lindasbakskola import LindasBakSkolaScraper

ALLOWED_DOMAINS = {
    "ica.se",
    "www.ica.se",
    "koket.se",
    "www.koket.se",
    "recept.nu",
    "www.recept.nu",
    "alltommat.expressen.se",
    "lindasbakskola.se",
    "www.lindasbakskola.se",
    "arla.se",
    "www.arla.se",
    "coop.se",
    "www.coop.se",
}

# Sites that need a custom HTML parser instead of (or as fallback after) JSON-LD
_CUSTOM_SCRAPERS = {
    "lindasbakskola.se": LindasBakSkolaScraper(),
    "www.lindasbakskola.se": LindasBakSkolaScraper(),
}

_json_ld_scraper = JsonLdScraper()


def _domain(url: str) -> str:
    return urlparse(url).netloc.lower()


def is_supported(url: str) -> bool:
    return _domain(url) in ALLOWED_DOMAINS


def scrape_url(url: str) -> ScraperResult:
    if not is_supported(url):
        supported = ", ".join(sorted(ALLOWED_DOMAINS))
        raise ScrapeError(f"Den här sajten stöds inte. Stödda sajter: {supported}")

    try:
        response = httpx.get(
            url,
            timeout=15,
            follow_redirects=True,
            headers={"User-Agent": "Mozilla/5.0 (compatible; RecipeKingBot/1.0)"},
        )
        response.raise_for_status()
    except httpx.HTTPError as exc:
        raise ScrapeError(f"Kunde inte hämta sidan: {exc}") from exc

    domain = _domain(str(response.url))
    html = response.text

    # Use custom scraper if available, otherwise fall back to JSON-LD
    if domain in _CUSTOM_SCRAPERS:
        result = _CUSTOM_SCRAPERS[domain].scrape(html, str(response.url))
    else:
        result = _json_ld_scraper.scrape(html, str(response.url))

    if not result or not result.ingredients:
        raise ScrapeError("Kunde inte tolka receptet från den här sidan.")
    return result
