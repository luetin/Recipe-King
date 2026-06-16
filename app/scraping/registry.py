from urllib.parse import urlparse

import httpx

from app.scraping.base import ScrapeError, ScraperResult
from app.scraping.jsonld import JsonLdScraper

# Domains confirmed to embed schema.org/Recipe JSON-LD, verified by fetching
# live recipe pages: ica.se and koket.se (recept.nu permanently redirects to
# koket.se). coop.se renders recipe content client-side via React with no
# server-rendered markup, so it isn't supported without a headless browser.
ALLOWED_DOMAINS = {
    "ica.se",
    "www.ica.se",
    "koket.se",
    "www.koket.se",
    "recept.nu",
    "www.recept.nu",
}

_json_ld_scraper = JsonLdScraper()


def _domain(url: str) -> str:
    return urlparse(url).netloc.lower()


def is_supported(url: str) -> bool:
    return _domain(url) in ALLOWED_DOMAINS


def scrape_url(url: str) -> ScraperResult:
    if not is_supported(url):
        supported = ", ".join(sorted({d for d in ALLOWED_DOMAINS if d.startswith("www.")}))
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

    result = _json_ld_scraper.scrape(response.text, str(response.url))
    if not result or not result.ingredients:
        raise ScrapeError("Kunde inte tolka receptet från den här sidan.")
    return result
