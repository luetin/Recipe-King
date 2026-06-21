from fastapi import APIRouter, Depends, Form, Request
from fastapi.templating import Jinja2Templates

from app.deps import require_login
from app.models import User
from app.scraping.base import ScrapeError
from app.scraping.registry import SITE_LABELS, scrape_url
from app.services.image_service import save_image_from_url

router = APIRouter(prefix="/recipes/import", tags=["import"])
templates = Jinja2Templates(directory="app/templates")


@router.post("/url")
async def import_url(
    request: Request,
    url: str = Form(...),
    current_user: User = Depends(require_login),
):
    try:
        result = scrape_url(url)
    except ScrapeError as exc:
        return templates.TemplateResponse(
            "recipes/import_url.html",
            {"request": request, "current_user": current_user, "error": str(exc), "site_labels": SITE_LABELS},
            status_code=400,
        )

    image_path = save_image_from_url(result.image_url) if result.image_url else None

    values = {
        "title": result.title,
        "description": result.description or "",
        "servings": result.servings or "",
        "prep_time_minutes": "",
        "cook_time_minutes": "",
        "ingredients_text": "\n".join(result.ingredients),
        "steps_text": "\n".join(result.steps),
    }

    return templates.TemplateResponse(
        "recipes/form.html",
        {
            "request": request,
            "current_user": current_user,
            "recipe": None,
            "values": values,
            "form_action": "/recipes/new",
            "prefill_notice": f"Receptet har hämtats från {result.source_url}. Granska och justera innan du sparar.",
            "prefill_image_path": image_path,
            "prefill_source_url": result.source_url,
        },
    )
