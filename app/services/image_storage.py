"""Stores uploaded maintenance photos on disk and builds their public URLs.

The file type is decided by sniffing the bytes, never by trusting the client's
filename or Content-Type. Files get random names, so URLs can't be guessed.
"""

from pathlib import Path
from uuid import uuid4

from app.config.settings import settings
from app.exceptions.app_exception import AppException

SUBDIR = "maintenance_images"


def storage_dir() -> Path:
    path = Path(settings.upload_dir) / SUBDIR
    path.mkdir(parents=True, exist_ok=True)
    return path


def detect_image_extension(content: bytes) -> str | None:
    if content.startswith(b"\xff\xd8\xff"):
        return "jpg"
    if content.startswith(b"\x89PNG\r\n\x1a\n"):
        return "png"
    if content[:4] == b"RIFF" and content[8:12] == b"WEBP":
        return "webp"
    return None


def public_url(filename: str) -> str:
    base = settings.app_base_url.rstrip("/")
    return f"{base}/uploads/{SUBDIR}/{filename}"


def save_image(content: bytes) -> str:
    """Validate and store the bytes. Returns the stored file's public URL."""
    if not content:
        raise AppException("Image file is empty", status_code=400)

    if len(content) > settings.max_image_bytes:
        limit_mb = settings.max_image_bytes // (1024 * 1024)
        raise AppException(
            f"Image is too large (maximum {limit_mb} MB)", status_code=413
        )

    extension = detect_image_extension(content)

    if extension is None:
        raise AppException(
            "Unsupported image type. Upload a JPEG, PNG or WebP file",
            status_code=415,
        )

    filename = f"{uuid4().hex}.{extension}"
    (storage_dir() / filename).write_bytes(content)
    return public_url(filename)


def delete_image_file(image_url: str) -> None:
    """Best effort removal of a file we stored (ignores external URLs)."""
    prefix = public_url("")

    if not image_url.startswith(prefix):
        return

    filename = Path(image_url[len(prefix):]).name
    (storage_dir() / filename).unlink(missing_ok=True)
