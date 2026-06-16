from fastapi import APIRouter, Depends, Request, UploadFile
from fastapi.templating import Jinja2Templates

from app.deps import require_login
from app.models import User
from app.services.file_import import extract_text, parse_recipe_text

router = APIRouter(prefix="/recipes/import", tags=["import"])
templates = Jinja2Templates(directory="app/templates")


@router.post("/file")
async def import_file(
    request: Request,
    file: UploadFile,
    current_user: User = Depends(require_login),
):
    data = await file.read()
    filename = file.filename or "uploaded"

    if not filename.lower().endswith((".pdf", ".txt")):
        return templates.TemplateResponse(
            "recipes/import_file.html",
            {"request": request, "current_user": current_user, "error": "Endast PDF- och textfiler stöds."},
            status_code=400,
        )

    text = extract_text(filename, data)
    if not text.strip():
        return templates.TemplateResponse(
            "recipes/import_file.html",
            {"request": request, "current_user": current_user, "error": "Kunde inte läsa någon text ur filen."},
            status_code=400,
        )

    fallback_title = filename.rsplit(".", 1)[0]
    parsed = parse_recipe_text(text, fallback_title)

    values = {
        "title": parsed.title,
        "description": "",
        "servings": "",
        "prep_time_minutes": "",
        "cook_time_minutes": "",
        "ingredients_text": "\n".join(parsed.ingredient_lines),
        "steps_text": "\n".join(parsed.step_lines),
    }

    return templates.TemplateResponse(
        "recipes/form.html",
        {
            "request": request,
            "current_user": current_user,
            "recipe": None,
            "values": values,
            "form_action": "/recipes/new",
            "prefill_notice": "Receptet har förifyllts från filen. Granska och justera innan du sparar.",
        },
    )
