from fastapi import Depends, Request
from sqlalchemy.orm import Session

from app.database import get_db
from app.models import User
from app.security import SESSION_COOKIE_NAME, read_session_value


class NotAuthenticated(Exception):
    """Raised by require_login; handled in main.py to redirect to /login."""


def get_current_user(request: Request, db: Session = Depends(get_db)) -> User | None:
    cookie = request.cookies.get(SESSION_COOKIE_NAME)
    if not cookie:
        return None
    user_id = read_session_value(cookie)
    if user_id is None:
        return None
    return db.get(User, user_id)


def require_login(user: User | None = Depends(get_current_user)) -> User:
    if user is None:
        raise NotAuthenticated()
    return user
