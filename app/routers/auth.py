from fastapi import APIRouter, Depends, Form, Request
from fastapi.responses import RedirectResponse
from fastapi.templating import Jinja2Templates
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.database import get_db
from app.deps import get_current_user
from app.models import User
from app.security import (
    SESSION_COOKIE_NAME,
    SESSION_MAX_AGE,
    create_session_value,
    hash_password,
    verify_password,
)

router = APIRouter()
templates = Jinja2Templates(directory="app/templates")


@router.get("/register")
def register_form(request: Request, current_user: User | None = Depends(get_current_user)):
    return templates.TemplateResponse(
        "auth/register.html", {"request": request, "current_user": current_user}
    )


@router.post("/register")
def register(
    request: Request,
    email: str = Form(...),
    password: str = Form(...),
    db: Session = Depends(get_db),
):
    user = User(email=email.strip().lower(), password_hash=hash_password(password))
    db.add(user)
    try:
        db.commit()
    except IntegrityError:
        db.rollback()
        return templates.TemplateResponse(
            "auth/register.html",
            {"request": request, "current_user": None, "error": "E-postadressen är redan registrerad."},
            status_code=400,
        )

    response = RedirectResponse(url="/recipes", status_code=303)
    response.set_cookie(
        SESSION_COOKIE_NAME,
        create_session_value(user.id),
        max_age=SESSION_MAX_AGE,
        httponly=True,
        samesite="lax",
    )
    return response


@router.get("/login")
def login_form(request: Request, current_user: User | None = Depends(get_current_user)):
    return templates.TemplateResponse(
        "auth/login.html", {"request": request, "current_user": current_user}
    )


@router.post("/login")
def login(
    request: Request,
    email: str = Form(...),
    password: str = Form(...),
    db: Session = Depends(get_db),
):
    user = db.query(User).filter(User.email == email.strip().lower()).first()
    if not user or not verify_password(password, user.password_hash):
        return templates.TemplateResponse(
            "auth/login.html",
            {"request": request, "current_user": None, "error": "Fel e-post eller lösenord."},
            status_code=400,
        )

    response = RedirectResponse(url="/recipes", status_code=303)
    response.set_cookie(
        SESSION_COOKIE_NAME,
        create_session_value(user.id),
        max_age=SESSION_MAX_AGE,
        httponly=True,
        samesite="lax",
    )
    return response


@router.post("/logout")
def logout():
    response = RedirectResponse(url="/login", status_code=303)
    response.delete_cookie(SESSION_COOKIE_NAME)
    return response
