import asyncio
import io

import cloudinary
import cloudinary.uploader
from fastapi import HTTPException, UploadFile
from PIL import Image, UnidentifiedImageError

from .config import get_settings

ALLOWED_TYPES = {"image/jpeg": "jpg", "image/png": "png", "image/webp": "webp"}


def configure() -> None:
    settings = get_settings()
    cloudinary.config(
        cloud_name=settings.cloudinary_cloud_name,
        api_key=settings.cloudinary_api_key,
        api_secret=settings.cloudinary_api_secret,
        secure=True,
    )


async def upload_product_image(image: UploadFile, vendor_id: int) -> dict:
    settings = get_settings()
    if not settings.cloudinary_enabled:
        raise HTTPException(503, "Product image storage is not configured")
    if image.content_type not in ALLOWED_TYPES:
        raise HTTPException(415, "Only JPEG, PNG and WebP images are accepted")
    payload = await image.read(settings.product_image_max_bytes + 1)
    if len(payload) > settings.product_image_max_bytes:
        raise HTTPException(413, "Image exceeds the configured upload limit")
    try:
        with Image.open(io.BytesIO(payload)) as parsed:
            parsed.verify()
    except (UnidentifiedImageError, OSError):
        raise HTTPException(422, "The uploaded file is not a valid image")
    configure()
    result = await asyncio.to_thread(
        cloudinary.uploader.upload,
        payload,
        folder=f"bloomai/vendors/{vendor_id}/products",
        resource_type="image",
        allowed_formats=list(ALLOWED_TYPES.values()),
        transformation=[{"width": 1400, "height": 1050, "crop": "limit", "quality": "auto", "fetch_format": "auto"}],
    )
    return {"image_url": result["secure_url"], "image_public_id": result["public_id"]}


async def delete_product_image(public_id: str | None) -> None:
    if not public_id or not get_settings().cloudinary_enabled:
        return
    configure()
    await asyncio.to_thread(cloudinary.uploader.destroy, public_id, invalidate=True)
