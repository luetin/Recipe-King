from fastapi import APIRouter, Depends, File, Form, HTTPException, Request, UploadFile
from fastapi.responses import RedirectResponse
from fastapi.templating import Jinja2Templates
from sqlalchemy.orm import Session

from app.database import get_db
from app.deps import get_current_user, require_login
from app.models import Recipe, User
from app.services import recipe_service
from app.services.image_service import save_uploaded_image

router = APIRouter(prefix="/recipes", tags=["recipes"])
templates = Jinja2Templates(directory="app/templates")


def _split_lines(text: str) -> list[str]:
    return [line for line in (l.strip() for l in text.splitlines()) if line]


def _split_tags(text: str) -> list[str]:
    return [tag for tag in (t.strip() for t in text.split(",")) if tag]


@router.get("")
def list_recipes(
    request: Request,
    q: str | None = None,
    tag: str | None = None,
    db: Session = Depends(get_db),
    current_user: User | None = Depends(get_current_user),
):
    recipes = recipe_service.list_recipes(db, search=q, tag=tag)
    return templates.TemplateResponse(
        "recipes/list.html",
        {"request": request, "current_user": current_user, "recipes": recipes, "search": q, "active_tag": tag},
    )


@router.get("/new")
def new_recipe_form(
    request: Request,
    current_user: User = Depends(require_login),
):
    return templates.TemplateResponse(
        "recipes/form.html",
        {"request": request, "current_user": current_user, "recipe": None, "form_action": "/recipes/new"},
    )


@router.post("/new")
def create_recipe(
    request: Request,
    title: str = Form(...),
    description: str = Form(""),
    servings: str = Form(""),
    prep_time_minutes: str = Form(""),
    cook_time_minutes: str = Form(""),
    ingredients_text: str = Form(""),
    steps_text: str = Form(""),
    notes: str = Form(""),
    tags_text: str = Form(""),
    image: UploadFile | None = File(None),
    prefill_image_path: str = Form(""),
    source_url: str = Form(""),
    current_user: User = Depends(require_login),
    db: Session = Depends(get_db),
):
    image_path = save_uploaded_image(image) if image and image.filename else (prefill_image_path or None)
    recipe = recipe_service.create_recipe(
        db,
        title=title,
        description=description or None,
        servings=servings or None,
        prep_time_minutes=int(prep_time_minutes) if prep_time_minutes else None,
        cook_time_minutes=int(cook_time_minutes) if cook_time_minutes else None,
        ingredient_lines=_split_lines(ingredients_text),
        step_lines=_split_lines(steps_text),
        notes=notes or None,
        tag_names=_split_tags(tags_text),
        created_by_id=current_user.id,
        image_path=image_path,
        source_url=source_url or None,
        source_type="scrape" if source_url else "manual",
    )
    return RedirectResponse(url=f"/recipes/{recipe.id}", status_code=303)


@router.get("/import/url")
def import_url_form(request: Request, current_user: User = Depends(require_login)):
    return templates.TemplateResponse(
        "recipes/import_url.html", {"request": request, "current_user": current_user}
    )


@router.get("/import/file")
def import_file_form(request: Request, current_user: User = Depends(require_login)):
    return templates.TemplateResponse(
        "recipes/import_file.html", {"request": request, "current_user": current_user}
    )


@router.get("/{recipe_id}")
def recipe_detail(
    recipe_id: int,
    request: Request,
    db: Session = Depends(get_db),
    current_user: User | None = Depends(get_current_user),
):
    recipe = recipe_service.get_recipe(db, recipe_id)
    if not recipe:
        raise HTTPException(status_code=404, detail="Recipe not found")

    def _group(items: list) -> list[tuple[str | None, list]]:
        grouped: list[tuple[str | None, list]] = []
        for item in items:
            if grouped and grouped[-1][0] == item.group_name:
                grouped[-1][1].append(item)
            else:
                grouped.append((item.group_name, [item]))
        return grouped

    grouped_steps_raw = _group(recipe.steps)
    grouped_steps: list[tuple[str | None, list[tuple[int, object]]]] = []
    step_number = 1
    for group_name, steps in grouped_steps_raw:
        numbered = []
        for step in steps:
            numbered.append((step_number, step))
            step_number += 1
        grouped_steps.append((group_name, numbered))

    avg_rating, rating_count = recipe_service.average_rating(recipe)
    user_rating = recipe_service.get_user_rating(recipe, current_user.id) if current_user else None

    return templates.TemplateResponse(
        "recipes/detail.html",
        {
            "request": request,
            "current_user": current_user,
            "recipe": recipe,
            "grouped_ingredients": _group(recipe.ingredients),
            "grouped_steps": grouped_steps,
            "avg_rating": avg_rating,
            "rating_count": rating_count,
            "user_rating": user_rating,
        },
    )


@router.get("/{recipe_id}/edit")
def edit_recipe_form(
    recipe_id: int,
    request: Request,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_login),
):
    recipe = recipe_service.get_recipe(db, recipe_id)
    if not recipe:
        raise HTTPException(status_code=404, detail="Recipe not found")
    if recipe.created_by_id != current_user.id:
        raise HTTPException(status_code=403, detail="Only the owner can edit this recipe")
    return templates.TemplateResponse(
        "recipes/form.html",
        {
            "request": request,
            "current_user": current_user,
            "recipe": recipe,
            "form_action": f"/recipes/{recipe.id}/edit",
        },
    )


@router.post("/{recipe_id}/edit")
def edit_recipe(
    recipe_id: int,
    title: str = Form(...),
    description: str = Form(""),
    servings: str = Form(""),
    prep_time_minutes: str = Form(""),
    cook_time_minutes: str = Form(""),
    ingredients_text: str = Form(""),
    steps_text: str = Form(""),
    notes: str = Form(""),
    tags_text: str = Form(""),
    image: UploadFile | None = File(None),
    current_user: User = Depends(require_login),
    db: Session = Depends(get_db),
):
    recipe = recipe_service.get_recipe(db, recipe_id)
    if not recipe:
        raise HTTPException(status_code=404, detail="Recipe not found")
    if recipe.created_by_id != current_user.id:
        raise HTTPException(status_code=403, detail="Only the owner can edit this recipe")

    image_path = save_uploaded_image(image) if image and image.filename else None
    recipe_service.update_recipe(
        db,
        recipe,
        title=title,
        description=description or None,
        servings=servings or None,
        prep_time_minutes=int(prep_time_minutes) if prep_time_minutes else None,
        cook_time_minutes=int(cook_time_minutes) if cook_time_minutes else None,
        ingredient_lines=_split_lines(ingredients_text),
        step_lines=_split_lines(steps_text),
        notes=notes or None,
        tag_names=_split_tags(tags_text),
        image_path=image_path,
    )
    return RedirectResponse(url=f"/recipes/{recipe.id}", status_code=303)


@router.post("/{recipe_id}/tags")
def add_tag(
    recipe_id: int,
    tag_name: str = Form(...),
    current_user: User = Depends(require_login),
    db: Session = Depends(get_db),
):
    recipe = recipe_service.get_recipe(db, recipe_id)
    if not recipe:
        raise HTTPException(status_code=404, detail="Recipe not found")
    if recipe.created_by_id != current_user.id:
        raise HTTPException(status_code=403, detail="Only the owner can edit this recipe")
    recipe_service.add_tag(db, recipe, tag_name)
    return RedirectResponse(url=f"/recipes/{recipe.id}", status_code=303)


@router.post("/{recipe_id}/tags/{tag_id}/delete")
def remove_tag(
    recipe_id: int,
    tag_id: int,
    current_user: User = Depends(require_login),
    db: Session = Depends(get_db),
):
    recipe = recipe_service.get_recipe(db, recipe_id)
    if not recipe:
        raise HTTPException(status_code=404, detail="Recipe not found")
    if recipe.created_by_id != current_user.id:
        raise HTTPException(status_code=403, detail="Only the owner can edit this recipe")
    recipe_service.remove_tag(db, recipe, tag_id)
    return RedirectResponse(url=f"/recipes/{recipe.id}", status_code=303)


@router.post("/{recipe_id}/rating")
def rate_recipe(
    recipe_id: int,
    score: int = Form(...),
    current_user: User = Depends(require_login),
    db: Session = Depends(get_db),
):
    if score < 1 or score > 5:
        raise HTTPException(status_code=400, detail="Score must be between 1 and 5")
    recipe = recipe_service.get_recipe(db, recipe_id)
    if not recipe:
        raise HTTPException(status_code=404, detail="Recipe not found")
    recipe_service.set_rating(db, recipe, current_user.id, score)
    return RedirectResponse(url=f"/recipes/{recipe.id}", status_code=303)


@router.post("/{recipe_id}/delete")
def delete_recipe(
    recipe_id: int,
    current_user: User = Depends(require_login),
    db: Session = Depends(get_db),
):
    recipe = recipe_service.get_recipe(db, recipe_id)
    if not recipe:
        raise HTTPException(status_code=404, detail="Recipe not found")
    if recipe.created_by_id != current_user.id:
        raise HTTPException(status_code=403, detail="Only the owner can delete this recipe")
    recipe_service.delete_recipe(db, recipe)
    return RedirectResponse(url="/recipes", status_code=303)
