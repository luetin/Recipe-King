import re

from bs4 import BeautifulSoup

from app.scraping.base import BaseScraper, ScraperResult

# Matches common Swedish cooking instruction section headers
_STEP_MARKERS = re.compile(
    r"(g[öo]r s[åa] h[äe]r|grilla den s[åa] h[äe]r|s[åa] h[äe]r gr[io]llar|tillv[äa]gag[åa]ngss[äa]tt|g[öo]r s[åa]\s*:)",
    re.I,
)
_INGREDIENT_MARKERS = re.compile(r"du beh[öo]ver|ingredienser\s*:", re.I)


def _text(el) -> str:
    return el.get_text(" ", strip=True)


class KottButikenScraper(BaseScraper):
    def scrape(self, html: str, url: str) -> ScraperResult | None:
        soup = BeautifulSoup(html, "lxml")

        title_el = soup.find("h1")
        title = _text(title_el) if title_el else None
        if not title:
            return None

        og_img = soup.find("meta", property="og:image")
        image_url = og_img["content"] if og_img and og_img.get("content") else None
        if image_url and image_url.startswith("//"):
            image_url = "https:" + image_url

        rte = soup.find(class_="rte")
        if not rte:
            return None

        ingredients: list[str] = []
        steps: list[str] = []
        description_parts: list[str] = []

        for p in rte.find_all("p"):
            # Replace <br> with newlines so we can split into lines
            for br in p.find_all("br"):
                br.replace_with("\n")
            full_text = p.get_text("\n")

            # Try to find section markers within the paragraph text
            step_match = _STEP_MARKERS.search(full_text)
            ing_match = _INGREDIENT_MARKERS.search(full_text)

            if step_match or ing_match:
                # Split at the marker
                if ing_match:
                    before = full_text[: ing_match.start()].strip()
                    after_ing = full_text[ing_match.end() :]
                    if before:
                        description_parts.append(before)
                    # If there's also a step marker after, split again
                    s2 = _STEP_MARKERS.search(after_ing)
                    if s2:
                        ing_block = after_ing[: s2.start()]
                        step_block = after_ing[s2.end() :]
                    else:
                        ing_block = after_ing
                        step_block = ""
                    for line in ing_block.splitlines():
                        line = line.strip()
                        if line:
                            ingredients.append(line)
                    for line in step_block.splitlines():
                        line = line.strip()
                        if line:
                            steps.append(line)
                elif step_match:
                    before = full_text[: step_match.start()].strip()
                    after_steps = full_text[step_match.end() :]
                    if before:
                        description_parts.append(before)
                    for line in after_steps.splitlines():
                        line = line.strip()
                        if line:
                            steps.append(line)
            else:
                # No marker — check for list items (ul/ol)
                if p.find(["ul", "ol"]):
                    continue  # handled separately below
                raw = full_text.strip()
                if raw:
                    description_parts.append(raw)

        # Handle list items — may be ingredients or steps
        for ul in rte.find_all(["ul", "ol"]):
            items = [_text(li) for li in ul.find_all("li") if _text(li)]
            if not ingredients:
                ingredients.extend(items)
            else:
                steps.extend(items)

        description = "\n\n".join(description_parts) or None

        if not steps and not ingredients:
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
