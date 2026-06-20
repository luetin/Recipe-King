import json
import re

from bs4 import BeautifulSoup

from app.scraping.base import BaseScraper, ScraperResult

_HTML_TAG_RE = re.compile(r"<[^>]+>")


def _strip_html(value: str) -> str:
    return _HTML_TAG_RE.sub("", value).strip()


def _as_list(value) -> list:
    if value is None:
        return []
    if isinstance(value, list):
        return value
    return [value]


def _find_recipe_node(data) -> dict | None:
    candidates = _as_list(data)
    for item in candidates:
        if not isinstance(item, dict):
            continue
        if "@graph" in item:
            found = _find_recipe_node(item["@graph"])
            if found:
                return found
        item_type = item.get("@type") or item.get("type")
        types = _as_list(item_type)
        if any(str(t).lower() == "recipe" for t in types):
            return item
    return None


def _extract_instructions(raw) -> list[str]:
    steps: list[str] = []
    for entry in _as_list(raw):
        if isinstance(entry, str):
            steps.append(_strip_html(entry))
        elif isinstance(entry, dict):
            entry_type = entry.get("@type") or entry.get("type")
            if entry_type == "HowToSection":
                section_name = entry.get("name")
                if section_name:
                    steps.append(f"{_strip_html(section_name)}:")
                steps.extend(_extract_instructions(entry.get("itemListElement", [])))
            else:
                text = entry.get("text") or entry.get("name") or ""
                if text:
                    steps.append(_strip_html(text))
    return [s for s in steps if s]


def _mark_step_headers(items: list[str]) -> list[str]:
    """Some sites (e.g. koket.se) flatten step section names ("Tartarsås",
    "Servering") as plain HowToStep entries with no HowToSection wrapper.
    Real steps are full sentences ending in punctuation; section names are
    short phrases with no trailing punctuation. Use that to detect headers
    and rewrite them as "Header:" using the same convention as ingredients.
    """
    marked = []
    for item in items:
        text = item.strip()
        if text.endswith(":"):
            marked.append(text)
        elif not text.endswith((".", "!", "?")) and len(text) <= 50:
            marked.append(f"{text}:")
        else:
            marked.append(text)
    return marked


def _mark_group_headers(items: list[str]) -> list[str]:
    """Some sites (e.g. koket.se) embed category headers as plain entries inside
    the flat recipeIngredient list, with no quantity, right before the first
    ingredient of that category. Detect them by lookahead: an item with no
    digits, immediately followed by an item that has digits, is almost always
    a header rather than a quantity-less ingredient (e.g. "salt"). Headers are
    rewritten as "Header:" so the existing group-header convention (used for
    manually typed ingredients) picks them up downstream.
    """
    marked = []
    for i, item in enumerate(items):
        text = item.strip()
        has_digit = any(ch.isdigit() for ch in text)
        next_has_digit = i + 1 < len(items) and any(ch.isdigit() for ch in items[i + 1])
        if not has_digit and next_has_digit and len(text) <= 40:
            marked.append(f"{text}:")
        else:
            marked.append(text)
    return marked


def _extract_image(raw) -> str | None:
    if raw is None:
        return None
    if isinstance(raw, str):
        return raw
    if isinstance(raw, dict):
        return raw.get("url")
    if isinstance(raw, list) and raw:
        return _extract_image(raw[0])
    return None


class JsonLdScraper(BaseScraper):
    def scrape(self, html: str, url: str) -> ScraperResult | None:
        soup = BeautifulSoup(html, "lxml")
        for script in soup.find_all("script", type="application/ld+json"):
            if not script.string:
                continue
            try:
                data = json.loads(script.string)
            except (json.JSONDecodeError, TypeError):
                continue
            recipe_node = _find_recipe_node(data)
            if not recipe_node:
                continue

            title = recipe_node.get("name")
            if not title:
                continue

            ingredients = [
                _strip_html(i) for i in _as_list(recipe_node.get("recipeIngredient")) if isinstance(i, str)
            ]
            ingredients = _mark_group_headers(ingredients)
            steps = _mark_step_headers(_extract_instructions(recipe_node.get("recipeInstructions")))
            servings = recipe_node.get("recipeYield")
            if isinstance(servings, list):
                servings = servings[0] if servings else None

            return ScraperResult(
                title=_strip_html(title),
                ingredients=ingredients,
                steps=steps,
                image_url=_extract_image(recipe_node.get("image")),
                servings=str(servings) if servings else None,
                source_url=url,
            )
        return None
