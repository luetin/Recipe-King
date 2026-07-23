import io
import uuid
from pathlib import Path

import httpx
from fastapi import UploadFile
from PIL import Image

from app.config import settings

MAX_DIMENSION = 1600
AVATAR_SIZE = 400
RECIPE_IMAGE_SUBDIR = "recipes"
AVATAR_IMAGE_SUBDIR = "avatars"


def _save_image_bytes(data: bytes, subdir: str = RECIPE_IMAGE_SUBDIR, max_dim: int = MAX_DIMENSION) -> str:
    image = Image.open(io.BytesIO(data))
    image = image.convert("RGB")
    if max(image.size) > max_dim:
        image.thumbnail((max_dim, max_dim))

    filename = f"{uuid.uuid4().hex}.jpg"
    target_dir = Path(settings.upload_dir) / subdir
    target_dir.mkdir(parents=True, exist_ok=True)
    target_path = target_dir / filename
    image.save(target_path, "JPEG", quality=85)

    return f"{subdir}/{filename}"


def save_uploaded_image(upload_file: UploadFile) -> str | None:
    data = upload_file.file.read()
    if not data:
        return None
    return _save_image_bytes(data)


def save_avatar_image(upload_file: UploadFile) -> str | None:
    data = upload_file.file.read()
    if not data:
        return None
    return _save_image_bytes(data, subdir=AVATAR_IMAGE_SUBDIR, max_dim=AVATAR_SIZE)


def save_image_from_url(url: str) -> str | None:
    try:
        response = httpx.get(url, timeout=10, follow_redirects=True)
        response.raise_for_status()
    except httpx.HTTPError:
        return None
    try:
        return _save_image_bytes(response.content)
    except Exception:
        return None
