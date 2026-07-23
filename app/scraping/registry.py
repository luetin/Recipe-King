from urllib.parse import urlparse

import httpx

from app.scraping.base import ScrapeError, ScraperResult
from app.scraping.jsonld import JsonLdScraper
from app.scraping.sites.bbqlovers import BbqLoversScraper
from app.scraping.sites.kottbutiken import KottButikenScraper
from app.scraping.sites.lindasbakskola import LindasBakSkolaScraper
from app.scraping.sites.wprm import WprmScraper

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
    "bbqlovers.se",
    "www.bbqlovers.se",
    "kottbutiken.com",
    "www.kottbutiken.com",
    "hankstruebbq.com",
    "www.hankstruebbq.com",
}

# Human-readable site labels shown on the import page
SITE_LABELS: list[tuple[str, str]] = [
    ("ICA", "ica.se"),
    ("Arla", "arla.se"),
    ("Coop", "coop.se"),
    ("Köket.se", "koket.se"),
    ("Recept.nu", "recept.nu"),
    ("Allt om mat", "alltommat.expressen.se"),
    ("Lindas bakskola", "lindasbakskola.se"),
    ("BBQ Lovers", "bbqlovers.se"),
    ("Köttbutiken", "kottbutiken.com"),
    ("Hank's True BBQ", "hankstruebbq.com"),
]

# Sites that need a custom HTML parser instead of (or as fallback after) JSON-LD
_CUSTOM_SCRAPERS = {
    "lindasbakskola.se": LindasBakSkolaScraper(),
    "www.lindasbakskola.se": LindasBakSkolaScraper(),
    "bbqlovers.se": BbqLoversScraper(),
    "www.bbqlovers.se": BbqLoversScraper(),
    "kottbutiken.com": KottButikenScraper(),
    "www.kottbutiken.com": KottButikenScraper(),
    "hankstruebbq.com": WprmScraper(),
    "www.hankstruebbq.com": WprmScraper(),
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
