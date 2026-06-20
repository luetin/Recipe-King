from fastapi import APIRouter, Depends, Form, HTTPException, Request
from fastapi.responses import RedirectResponse
from fastapi.templating import Jinja2Templates
from sqlalchemy.orm import Session

from app.database import get_db
from app.deps import get_current_user, require_login
from app.models import User
from app.services import collection_service, recipe_service

router = APIRouter(prefix="/collections", tags=["collections"])
templates = Jinja2Templates(directory="app/templates")


@router.get("")
def list_collections(
    request: Request,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_login),
):
    collections = collection_service.list_collections(db, current_user.id)
    return templates.TemplateResponse(
        "collections/list.html",
        {"request": request, "current_user": current_user, "collections": collections},
    )


@router.post("/new")
def create_collection(
    name: str = Form(...),
    description: str = Form(""),
    db: Session = Depends(get_db),
    current_user: User = Depends(require_login),
):
    c = collection_service.create_collection(db, current_user.id, name, description or None)
    return RedirectResponse(url=f"/collections/{c.id}", status_code=303)


@router.get("/{collection_id}")
def collection_detail(
    collection_id: int,
    request: Request,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_login),
):
    c = collection_service.get_collection(db, collection_id)
    if not c:
        raise HTTPException(status_code=404, detail="Samling hittades inte")
    if c.user_id != current_user.id:
        raise HTTPException(status_code=403, detail="Åtkomst nekad")
    return templates.TemplateResponse(
        "collections/detail.html",
        {"request": request, "current_user": current_user, "collection": c},
    )


@router.post("/{collection_id}/delete")
def delete_collection(
    collection_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_login),
):
    c = collection_service.get_collection(db, collection_id)
    if not c:
        raise HTTPException(status_code=404, detail="Samling hittades inte")
    if c.user_id != current_user.id:
        raise HTTPException(status_code=403, detail="Åtkomst nekad")
    collection_service.delete_collection(db, c)
    return RedirectResponse(url="/collections", status_code=303)


@router.post("/{collection_id}/recipes/{recipe_id}/add")
def add_recipe_to_collection(
    collection_id: int,
    recipe_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_login),
):
    c = collection_service.get_collection(db, collection_id)
    if not c or c.user_id != current_user.id:
        raise HTTPException(status_code=403, detail="Åtkomst nekad")
    recipe = recipe_service.get_recipe(db, recipe_id)
    if not recipe:
        raise HTTPException(status_code=404, detail="Recept hittades inte")
    collection_service.add_recipe(db, c, recipe)
    return RedirectResponse(url=f"/recipes/{recipe_id}", status_code=303)


@router.post("/{collection_id}/recipes/{recipe_id}/remove")
def remove_recipe_from_collection(
    collection_id: int,
    recipe_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_login),
):
    c = collection_service.get_collection(db, collection_id)
    if not c or c.user_id != current_user.id:
        raise HTTPException(status_code=403, detail="Åtkomst nekad")
    recipe = recipe_service.get_recipe(db, recipe_id)
    if recipe:
        collection_service.remove_recipe(db, c, recipe)
    return RedirectResponse(url=f"/collections/{collection_id}", status_code=303)
