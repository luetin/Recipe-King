import uuid

from fastapi import APIRouter, Depends, Form, HTTPException, Request
from fastapi.responses import RedirectResponse
from fastapi.templating import Jinja2Templates
from sqlalchemy.orm import Session

from app.database import get_db
from app.deps import get_current_user
from app.models import User
from app.security import SESSION_COOKIE_NAME, SESSION_MAX_AGE, create_session_value

router = APIRouter()
templates = Jinja2Templates(directory="app/templates")


def _set_session(response, user_id: int):
    response.set_cookie(
        SESSION_COOKIE_NAME,
        create_session_value(user_id),
        max_age=SESSION_MAX_AGE,
        httponly=True,
        samesite="lax",
    )


@router.get("/login")
def login_page(
    request: Request,
    db: Session = Depends(get_db),
    current_user: User | None = Depends(get_current_user),
):
    if current_user:
        return RedirectResponse(url="/recipes", status_code=303)
    users = db.query(User).order_by(User.display_name, User.email).all()
    return templates.TemplateResponse(
        "auth/login.html",
        {"request": request, "current_user": None, "users": users},
    )


@router.post("/login/{user_id}")
def login_as(
    user_id: int,
    db: Session = Depends(get_db),
):
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404)
    response = RedirectResponse(url="/recipes", status_code=303)
    _set_session(response, user.id)
    return response


@router.get("/register")
def register_form(request: Request, current_user: User | None = Depends(get_current_user)):
    return RedirectResponse(url="/login", status_code=303)


@router.post("/register")
def create_profile(
    request: Request,
    display_name: str = Form(...),
    db: Session = Depends(get_db),
):
    name = display_name.strip()
    if not name:
        users = db.query(User).order_by(User.display_name, User.email).all()
        return templates.TemplateResponse(
            "auth/login.html",
            {"request": request, "current_user": None, "users": users, "error": "Ange ett namn."},
            status_code=400,
        )
    # Generate a unique internal email so the unique constraint is satisfied
    slug = name.lower().replace(" ", "_")
    email = f"{slug}_{uuid.uuid4().hex[:6]}@local"
    user = User(display_name=name, email=email, password_hash=None)
    db.add(user)
    db.commit()
    db.refresh(user)
    response = RedirectResponse(url="/recipes", status_code=303)
    _set_session(response, user.id)
    return response


@router.post("/logout")
def logout():
    response = RedirectResponse(url="/login", status_code=303)
    response.delete_cookie(SESSION_COOKIE_NAME)
    return response
