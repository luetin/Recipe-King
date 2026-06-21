from dataclasses import dataclass, field


@dataclass
class ScraperResult:
    title: str
    ingredients: list[str] = field(default_factory=list)
    steps: list[str] = field(default_factory=list)
    image_url: str | None = None
    servings: str | None = None
    source_url: str = ""
    description: str | None = None


class ScrapeError(Exception):
    pass


class BaseScraper:
    def scrape(self, html: str, url: str) -> ScraperResult | None:
        raise NotImplementedError
