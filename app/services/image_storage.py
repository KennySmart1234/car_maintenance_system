"""Validate and store uploaded images using Cloudinary."""

from uuid import uuid4

import cloudinary
import cloudinary.uploader

from app.config.settings import settings
from app.exceptions.app_exception import AppException


SUBDIR = "maintenance_images"


cloudinary.config(
    cloud_name=settings.cloudinary_cloud_name,
    api_key=settings.cloudinary_api_key,
    api_secret=settings.cloudinary_api_secret,
    secure=True,
)


def detect_image_extension(content: bytes) -> str | None:
    if content.startswith(b"\xff\xd8\xff"):
        return "jpg"

    if content.startswith(b"\x89PNG\r\n\x1a\n"):
        return "png"

    if content[:4] == b"RIFF" and content[8:12] == b"WEBP":
        return "webp"

    return None


def save_image(content: bytes) -> str:
    """Validate and upload image bytes to Cloudinary.

    Returns the permanent Cloudinary HTTPS URL.
    """
    if not content:
        raise AppException("Image file is empty", status_code=400)

    if len(content) > settings.max_image_bytes:
        limit_mb = settings.max_image_bytes // (1024 * 1024)
        raise AppException(
            f"Image is too large (maximum {limit_mb} MB)",
            status_code=413,
        )

    extension = detect_image_extension(content)

    if extension is None:
        raise AppException(
            "Unsupported image type. Upload a JPEG, PNG or WebP file",
            status_code=415,
        )

    public_id = f"{SUBDIR}/{uuid4().hex}"

    try:
        result = cloudinary.uploader.upload(
            content,
            public_id=public_id,
            resource_type="image",
        )
    except Exception as exc:
        raise AppException(
            "Failed to upload image",
            status_code=502,
        ) from exc

    secure_url = result.get("secure_url")

    if not secure_url:
        raise AppException(
            "Image upload did not return a public URL",
            status_code=502,
        )

    return secure_url


def delete_image_file(image_url: str) -> None:
    """Best-effort deletion of a Cloudinary image.

    External URLs are ignored.
    """
    if "res.cloudinary.com" not in image_url:
        return

    try:
        public_id = image_url.split("/image/upload/")[-1]
        public_id = public_id.rsplit(".", 1)[0]

        cloudinary.uploader.destroy(
            public_id,
            resource_type="image",
        )
    except Exception:
        pass