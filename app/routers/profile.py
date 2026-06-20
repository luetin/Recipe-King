from fastapi import APIRouter, Depends, Form, Request
from fastapi.responses import RedirectResponse
from fastapi.templating import Jinja2Templates
from sqlalchemy.orm import Session

from app.database import get_db
from app.deps import require_login
from app.models import User
from app.security import hash_password, verify_password

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
    db: Session = Depends(get_db),
    current_user: User = Depends(require_login),
):
    user = db.query(User).filter(User.id == current_user.id).first()

    if display_name.strip():
        user.display_name = display_name.strip()
    else:
        user.display_name = None

    if new_password:
        if not current_password or not verify_password(current_password, user.password_hash):
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
