import re
from dataclasses import dataclass, field

import pdfplumber

INGREDIENT_HEADERS = ("ingredienser", "ingredients", "du behöver", "du behover")
STEP_HEADERS = ("instruktioner", "gör så här", "gor sa har", "tillagning", "steps", "method", "directions")

_QUANTITY_RE = re.compile(
    r"^(?P<quantity>\d+[\d/.,\-–]*)\s*(?P<unit>dl|g|kg|ml|l|msk|tsk|st|cl|krm)?\.?\s+(?P<name>.+)$",
    re.IGNORECASE,
)
_NUMBERED_RE = re.compile(r"^\d+[.)]\s*")


@dataclass
class ParsedRecipe:
    title: str
    ingredient_lines: list[str] = field(default_factory=list)
    step_lines: list[str] = field(default_factory=list)
    raw_text: str = ""


def extract_text(filename: str, data: bytes) -> str:
    if filename.lower().endswith(".pdf"):
        text_parts: list[str] = []
        import io

        with pdfplumber.open(io.BytesIO(data)) as pdf:
            for page in pdf.pages:
                page_text = page.extract_text() or ""
                text_parts.append(page_text)
        return "\n".join(text_parts)
    return data.decode("utf-8", errors="replace")


def _is_header(line: str, keywords: tuple[str, ...]) -> bool:
    lowered = line.strip().lower().rstrip(":")
    return lowered in keywords


def parse_recipe_text(text: str, fallback_title: str) -> ParsedRecipe:
    lines = [line.strip() for line in text.splitlines()]
    lines = [line for line in lines if line]

    if not lines:
        return ParsedRecipe(title=fallback_title, raw_text=text)

    ingredient_start = next(
        (i for i, line in enumerate(lines) if _is_header(line, INGREDIENT_HEADERS)), None
    )
    step_start = next((i for i, line in enumerate(lines) if _is_header(line, STEP_HEADERS)), None)

    if ingredient_start is None or step_start is None or step_start <= ingredient_start:
        # Heuristics didn't find clear sections; treat first line as title only.
        title = lines[0]
        return ParsedRecipe(title=title, raw_text=text)

    title = lines[0] if ingredient_start > 0 else fallback_title
    ingredient_lines = [_clean_ingredient_line(l) for l in lines[ingredient_start + 1 : step_start]]
    step_lines = [_clean_step_line(l) for l in lines[step_start + 1 :]]

    return ParsedRecipe(
        title=title,
        ingredient_lines=ingredient_lines,
        step_lines=step_lines,
        raw_text=text,
    )


def _clean_ingredient_line(line: str) -> str:
    return line


def _clean_step_line(line: str) -> str:
    return _NUMBERED_RE.sub("", line).strip()


def parse_ingredient_components(raw_text: str) -> tuple[str | None, str | None, str | None]:
    match = _QUANTITY_RE.match(raw_text)
    if not match:
        return None, None, raw_text
    return match.group("quantity"), match.group("unit"), match.group("name")
