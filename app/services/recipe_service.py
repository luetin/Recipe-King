from sqlalchemy import func, or_
from sqlalchemy.orm import Session, joinedload

from app.models import Ingredient, Rating, Recipe, Step, Tag, recipe_tags


def list_all_tags(db: Session) -> list[tuple[str, int]]:
    """Return all tags sorted by usage count descending, as (name, count) tuples."""
    rows = (
        db.query(Tag.name, func.count(recipe_tags.c.recipe_id).label("cnt"))
        .outerjoin(recipe_tags, Tag.id == recipe_tags.c.tag_id)
        .group_by(Tag.id, Tag.name)
        .order_by(func.count(recipe_tags.c.recipe_id).desc(), Tag.name)
        .all()
    )
    return [(name, cnt) for name, cnt in rows]


def list_recipes(db: Session, search: str | None = None, tag: str | None = None) -> list[Recipe]:
    query = db.query(Recipe).options(joinedload(Recipe.created_by), joinedload(Recipe.tags))
    if search:
        query = query.filter(
            or_(
                Recipe.title.ilike(f"%{search}%"),
                Recipe.description.ilike(f"%{search}%"),
                Recipe.tags.any(Tag.name.ilike(f"%{search}%")),
            )
        )
    if tag:
        query = query.filter(Recipe.tags.any(Tag.name == tag))
    return query.order_by(Recipe.created_at.desc()).all()


def get_recipe(db: Session, recipe_id: int) -> Recipe | None:
    return (
        db.query(Recipe)
        .options(
            joinedload(Recipe.ingredients),
            joinedload(Recipe.steps),
            joinedload(Recipe.created_by),
            joinedload(Recipe.tags),
            joinedload(Recipe.ratings),
        )
        .filter(Recipe.id == recipe_id)
        .first()
    )


def _is_group_header(line: str) -> bool:
    return line.endswith(":") and len(line) <= 60


def _set_ingredients(recipe: Recipe, raw_lines: list[str]) -> None:
    recipe.ingredients.clear()
    current_group: str | None = None
    order = 0
    for line in raw_lines:
        line = line.strip()
        if not line:
            continue
        if _is_group_header(line):
            current_group = line.rstrip(":").strip()
            continue
        recipe.ingredients.append(Ingredient(raw_text=line, order=order, group_name=current_group))
        order += 1


def _set_steps(recipe: Recipe, raw_lines: list[str]) -> None:
    recipe.steps.clear()
    current_group: str | None = None
    order = 0
    for line in raw_lines:
        line = line.strip()
        if not line:
            continue
        if _is_group_header(line):
            current_group = line.rstrip(":").strip()
            continue
        recipe.steps.append(Step(text=line, order=order, group_name=current_group))
        order += 1


def _resolve_tags(db: Session, tag_names: list[str]) -> list[Tag]:
    tags = []
    for raw_name in tag_names:
        name = raw_name.strip().lower()
        if not name:
            continue
        tag = db.query(Tag).filter(Tag.name == name).first()
        if not tag:
            tag = Tag(name=name)
            db.add(tag)
        tags.append(tag)
    return tags


def create_recipe(
    db: Session,
    *,
    title: str,
    description: str | None,
    servings: str | None,
    prep_time_minutes: int | None,
    cook_time_minutes: int | None,
    ingredient_lines: list[str],
    step_lines: list[str],
    created_by_id: int,
    notes: str | None = None,
    tag_names: list[str] | None = None,
    image_path: str | None = None,
    source_url: str | None = None,
    source_type: str = "manual",
    raw_import_text: str | None = None,
) -> Recipe:
    recipe = Recipe(
        title=title,
        description=description,
        servings=servings,
        prep_time_minutes=prep_time_minutes,
        cook_time_minutes=cook_time_minutes,
        created_by_id=created_by_id,
        notes=notes,
        image_path=image_path,
        source_url=source_url,
        source_type=source_type,
        raw_import_text=raw_import_text,
    )
    _set_ingredients(recipe, ingredient_lines)
    _set_steps(recipe, step_lines)
    recipe.tags = _resolve_tags(db, tag_names or [])
    db.add(recipe)
    db.commit()
    db.refresh(recipe)
    return recipe


def update_recipe(
    db: Session,
    recipe: Recipe,
    *,
    title: str,
    description: str | None,
    servings: str | None,
    prep_time_minutes: int | None,
    cook_time_minutes: int | None,
    ingredient_lines: list[str],
    step_lines: list[str],
    notes: str | None = None,
    tag_names: list[str] | None = None,
    image_path: str | None = None,
) -> Recipe:
    recipe.title = title
    recipe.description = description
    recipe.servings = servings
    recipe.prep_time_minutes = prep_time_minutes
    recipe.cook_time_minutes = cook_time_minutes
    recipe.notes = notes
    if image_path:
        recipe.image_path = image_path
    _set_ingredients(recipe, ingredient_lines)
    _set_steps(recipe, step_lines)
    if tag_names is not None:
        recipe.tags = _resolve_tags(db, tag_names)
    db.commit()
    db.refresh(recipe)
    return recipe


def delete_recipe(db: Session, recipe: Recipe) -> None:
    db.delete(recipe)
    db.commit()


def add_tag(db: Session, recipe: Recipe, tag_name: str) -> None:
    name = tag_name.strip().lower()
    if not name:
        return
    tag = db.query(Tag).filter(Tag.name == name).first()
    if not tag:
        tag = Tag(name=name)
        db.add(tag)
    if tag not in recipe.tags:
        recipe.tags.append(tag)
    db.commit()


def remove_tag(db: Session, recipe: Recipe, tag_id: int) -> None:
    recipe.tags = [t for t in recipe.tags if t.id != tag_id]
    db.commit()


def average_rating(recipe: Recipe) -> tuple[float | None, int]:
    scores = [r.score for r in recipe.ratings]
    if not scores:
        return None, 0
    return sum(scores) / len(scores), len(scores)


def get_user_rating(recipe: Recipe, user_id: int) -> int | None:
    for r in recipe.ratings:
        if r.user_id == user_id:
            return r.score
    return None


def set_rating(db: Session, recipe: Recipe, user_id: int, score: int) -> None:
    rating = db.query(Rating).filter(Rating.recipe_id == recipe.id, Rating.user_id == user_id).first()
    if rating:
        rating.score = score
    else:
        db.add(Rating(recipe_id=recipe.id, user_id=user_id, score=score))
    db.commit()
