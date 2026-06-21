import re

from bs4 import BeautifulSoup

from app.scraping.base import BaseScraper, ScraperResult

_INGREDIENT_MARKERS = re.compile(r"du beh[öo]ver|ingredienser", re.I)
_STEP_MARKERS = re.compile(r"g[öo]r s[åa] h[äe]r|tillv[äa]gag[åa]ngss[äa]tt|instruktioner", re.I)
_HTML_TAG = re.compile(r"<[^>]+>")


def _text(el) -> str:
    return el.get_text(" ", strip=True)


class BbqLoversScraper(BaseScraper):
    def scrape(self, html: str, url: str) -> ScraperResult | None:
        soup = BeautifulSoup(html, "lxml")

        title_el = soup.find("h1")
        title = _text(title_el) if title_el else None
        if not title:
            return None

        og_img = soup.find("meta", property="og:image")
        image_url = og_img["content"] if og_img and og_img.get("content") else None

        content = soup.find(class_="td-post-content")
        if not content:
            return None

        ingredients: list[str] = []
        steps: list[str] = []
        description_parts: list[str] = []
        mode = "intro"

        for p in content.find_all("p"):
            # Check if this paragraph contains a section marker in a strong/span
            strong_text = " ".join(s.get_text(" ", strip=True) for s in p.find_all(["strong", "b"]))
            raw_text = _text(p)

            if _INGREDIENT_MARKERS.search(strong_text):
                mode = "ingredients"
                continue
            if _STEP_MARKERS.search(strong_text):
                mode = "steps"
                continue

            # Skip empty paragraphs and image-only paragraphs
            if not raw_text or p.find("img") and not raw_text:
                continue

            if mode == "intro":
                if raw_text:
                    description_parts.append(raw_text)
            elif mode == "ingredients":
                # Each non-empty paragraph is one ingredient
                if raw_text and not p.find("img"):
                    ingredients.append(raw_text)
            elif mode == "steps":
                # Paragraphs may contain <br> — split into separate steps
                if p.find("img"):
                    continue
                # Replace <br> with newline then split
                for br in p.find_all("br"):
                    br.replace_with("\n")
                for line in p.get_text("\n", strip=True).splitlines():
                    line = line.strip()
                    if line:
                        steps.append(line)

        description = " ".join(description_parts) or None

        if not ingredients and not steps:
            return None

        return ScraperResult(
            title=title,
            ingredients=ingredients,
            steps=steps,
            image_url=image_url,
            servings=None,
            source_url=url,
            description=description,
        )
