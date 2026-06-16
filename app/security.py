from itsdangerous import BadSignature, URLSafeTimedSerializer
from passlib.context import CryptContext

from app.config import settings

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
_serializer = URLSafeTimedSerializer(settings.secret_key, salt="session")

SESSION_COOKIE_NAME = "session"
SESSION_MAX_AGE = 60 * 60 * 24 * 30  # 30 days


def hash_password(password: str) -> str:
    return pwd_context.hash(password)


def verify_password(password: str, password_hash: str) -> bool:
    return pwd_context.verify(password, password_hash)


def create_session_value(user_id: int) -> str:
    return _serializer.dumps({"user_id": user_id})


def read_session_value(value: str) -> int | None:
    try:
        data = _serializer.loads(value, max_age=SESSION_MAX_AGE)
    except BadSignature:
        return None
    return data.get("user_id")
