"""Scraper for sites using WP Recipe Maker (WPRM) plugin."""
import re

from bs4 import BeautifulSoup

from app.scraping.base import BaseScraper, ScraperResult


def _text(el) -> str:
    return el.get_text(" ", strip=True) if el else ""


class WprmScraper(BaseScraper):
    def scrape(self, html: str, url: str) -> ScraperResult | None:
        soup = BeautifulSoup(html, "lxml")

        container = soup.find(class_=re.compile(r"wprm-recipe-container"))
        if not container:
            return None

        # Title
        title_el = container.find(class_=re.compile(r"wprm-recipe-name"))
        title = _text(title_el) if title_el else None
        if not title:
            h1 = soup.find("h1")
            title = _text(h1) if h1 else None
        if not title:
            return None

        # Servings
        srv_el = container.find(class_=re.compile(r"wprm-recipe-servings\b"))
        servings = _text(srv_el) if srv_el else None
        srv_unit = container.find(class_=re.compile(r"wprm-recipe-servings-unit"))
        if srv_unit and servings:
            servings = f"{servings} {_text(srv_unit)}"

        # Image — prefer OG image (higher res)
        og = soup.find("meta", property="og:image")
        image_url = og["content"] if og and og.get("content") else None
        if not image_url:
            img_wrap = container.find(class_=re.compile(r"wprm-recipe-image"))
            if img_wrap:
                img = img_wrap.find("img")
                image_url = img.get("src") if img else None

        # Description
        desc_el = container.find(class_=re.compile(r"wprm-recipe-summary"))
        description = _text(desc_el) if desc_el else None

        # Ingredients
        ingredients: list[str] = []
        ing_container = container.find(class_=re.compile(r"wprm-recipe-ingredients-container"))
        if ing_container:
            for group in ing_container.find_all(class_=re.compile(r"wprm-recipe-ingredient-group\b")):
                group_name_el = group.find(class_=re.compile(r"wprm-recipe-ingredient-group-name"))
                if group_name_el:
                    gname = _text(group_name_el).rstrip(":")
                    if gname:
                        ingredients.append(f"{gname}:")

                for li in group.find_all("li", class_=re.compile(r"wprm-recipe-ingredient\b")):
                    parts = []
                    amount = li.find(class_=re.compile(r"wprm-recipe-ingredient-amount"))
                    unit = li.find(class_=re.compile(r"wprm-recipe-ingredient-unit"))
                    name = li.find(class_=re.compile(r"wprm-recipe-ingredient-name"))
                    notes = li.find(class_=re.compile(r"wprm-recipe-ingredient-notes"))
                    if amount:
                        parts.append(_text(amount))
                    if unit:
                        parts.append(_text(unit))
                    if name:
                        parts.append(_text(name))
                    if notes:
                        parts.append(f"({_text(notes).strip('()')})")
                    line = " ".join(parts).strip()
                    if line:
                        ingredients.append(line)

        # Instructions
        steps: list[str] = []
        inst_container = container.find(class_=re.compile(r"wprm-recipe-instructions-container"))
        if inst_container:
            for group in inst_container.find_all(class_=re.compile(r"wprm-recipe-instruction-group\b")):
                group_name_el = group.find(class_=re.compile(r"wprm-recipe-instruction-group-name"))
                if group_name_el:
                    gname = _text(group_name_el).rstrip(":")
                    if gname:
                        steps.append(f"{gname}:")

                for li in group.find_all("li", class_=re.compile(r"wprm-recipe-instruction\b")):
                    text_el = li.find(class_=re.compile(r"wprm-recipe-instruction-text"))
                    text = _text(text_el) if text_el else _text(li)
                    if text:
                        steps.append(text)

            # Flat list fallback (no groups)
            if not steps:
                for li in inst_container.find_all("li", class_=re.compile(r"wprm-recipe-instruction\b")):
                    text_el = li.find(class_=re.compile(r"wprm-recipe-instruction-text"))
                    text = _text(text_el) if text_el else _text(li)
                    if text:
                        steps.append(text)

        if not ingredients and not steps:
            return None

        return ScraperResult(
            title=title,
            ingredients=ingredients,
            steps=steps,
            image_url=image_url,
            servings=servings,
            source_url=url,
            description=description,
        )
