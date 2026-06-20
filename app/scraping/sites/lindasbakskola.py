import json
import re

from bs4 import BeautifulSoup

from app.scraping.base import BaseScraper, ScraperResult

# Ingredient group headers are short, bold-only labels with no trailing sentence punctuation
_GROUP_RE = re.compile(r"^[^.!?]{1,50}$")
_STEP_NUM_RE = re.compile(r"^\d+\.")
_SERVINGS_RE = re.compile(r"^\d")


class LindasBakSkolaScraper(BaseScraper):
    """
    Parser for lindasbakskola.se recipes.
    JSON-LD has title/image but no ingredients or instructions;
    those are in the article HTML:
      - <h1>                           recipe title
      - <p><strong>N st</strong>       servings
      - <p><em>ingredient</em><br/>…   ingredients (one or more per <p>)
      - <p><strong>Group</strong>      ingredient group header (short, no sentence punct)
           followed by <br/><em>…     group members in same <p>
      - <p><strong>GÖR SÅ HÄR</strong>  marks start of steps
      - <p><strong>1.</strong> text    numbered step
    """

    def scrape(self, html: str, url: str) -> ScraperResult | None:
        soup = BeautifulSoup(html, "lxml")

        article = soup.find("article") or soup.find(class_=re.compile(r"entry-content|post-content"))
        if not article:
            return None

        h1 = article.find("h1")
        if not h1:
            return None
        title = h1.get_text(strip=True)

        # Image from JSON-LD (populated there even though ingredients/steps aren't)
        image_url = None
        for script in soup.find_all("script", type="application/ld+json"):
            try:
                data = json.loads(script.string or "")
                for item in ([data] if isinstance(data, dict) else data or []):
                    if isinstance(item, dict) and item.get("@type") == "Recipe":
                        img = item.get("image")
                        if isinstance(img, str):
                            image_url = img
                        elif isinstance(img, dict):
                            image_url = img.get("url")
                        elif isinstance(img, list) and img:
                            image_url = img[0] if isinstance(img[0], str) else img[0].get("url")
            except Exception:
                pass

        servings: str | None = None
        ingredients: list[str] = []
        steps: list[str] = []
        in_steps = False

        for p in h1.find_all_next("p"):
            strong = p.find("strong")
            strong_text = strong.get_text(strip=True) if strong else ""
            em_items = [em.get_text(strip=True) for em in p.find_all("em") if em.get_text(strip=True)]

            # Detect start of instructions section
            if "GÖR SÅ HÄR" in strong_text.upper():
                in_steps = True
                continue

            if in_steps:
                if strong and _STEP_NUM_RE.match(strong_text):
                    full = p.get_text(" ", strip=True)
                    # Strip WordPress [caption]...[/caption] shortcodes
                    full = re.sub(r"\[caption[^\]]*\].*?\[/caption\]", "", full, flags=re.DOTALL)
                    step_text = re.sub(r"^\d+\.\s*", "", full).strip()
                    # Remove any trailing caption lines
                    step_text = step_text.split("[caption")[0].strip()
                    if step_text:
                        steps.append(step_text)
                continue

            # --- ingredient section ---

            # Servings: first bold-only line starting with a digit
            if servings is None and strong and _SERVINGS_RE.match(strong_text) and not em_items:
                servings = strong_text
                continue

            # Skip tip/note paragraphs (bold text ending with ! or containing "TIPS")
            if strong and ("TIPS" in strong_text.upper() or strong_text.endswith("!")):
                continue

            # Ingredient group header: short bold text with no sentence-ending punctuation
            # May also have em items on the same <p> (like "Garnering\n<em>vetemjöl</em>")
            if strong and _GROUP_RE.match(strong_text) and not strong_text[-1] in ".!?" if strong_text else False:
                ingredients.append(f"{strong_text}:")
                for line in em_items:
                    ingredients.append(line)
                continue

            # Plain ingredient lines in <em>
            for line in em_items:
                ingredients.append(line)

        if not ingredients or not steps:
            return None

        return ScraperResult(
            title=title,
            ingredients=ingredients,
            steps=steps,
            image_url=image_url,
            servings=servings,
            source_url=url,
        )
