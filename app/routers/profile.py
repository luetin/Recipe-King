from fastapi import APIRouter, Depends, File, Form, Request, UploadFile
from fastapi.responses import RedirectResponse
from fastapi.templating import Jinja2Templates
from sqlalchemy.orm import Session

from app.database import get_db
from app.deps import require_login
from app.models import User
from app.security import hash_password, verify_password
from app.services.image_service import save_avatar_image

router = APIRouter(prefix="/profile", tags=["profile"])
templates = Jinja2Templates(directory="app/templates")


@router.get("")
def profile_page(
    request: Request,
    current_user: User = Depends(require_login),
):
    return templates.TemplateResponse(
        "profile.html",
        {"request": request, "current_user": current_user},
    )


@router.post("")
def update_profile(
    request: Request,
    display_name: str = Form(""),
    current_password: str = Form(""),
    new_password: str = Form(""),
    avatar: UploadFile | None = File(None),
    db: Session = Depends(get_db),
    current_user: User = Depends(require_login),
):
    user = db.query(User).filter(User.id == current_user.id).first()

    if display_name.strip():
        user.display_name = display_name.strip()
    else:
        user.display_name = None

    if avatar and avatar.filename:
        path = save_avatar_image(avatar)
        if path:
            user.avatar_path = path

    if new_password:
        if user.password_hash and (not current_password or not verify_password(current_password, user.password_hash)):
            return templates.TemplateResponse(
                "profile.html",
                {
                    "request": request,
                    "current_user": current_user,
                    "error": "Nuvarande lösenord stämmer inte.",
                },
                status_code=400,
            )
        user.password_hash = hash_password(new_password)

    db.commit()
    return RedirectResponse(url="/profile?saved=1", status_code=303)


@router.post("/avatar/remove")
def remove_avatar(
    db: Session = Depends(get_db),
    current_user: User = Depends(require_login),
):
    user = db.query(User).filter(User.id == current_user.id).first()
    user.avatar_path = None
    db.commit()
    return RedirectResponse(url="/profile", status_code=303)
