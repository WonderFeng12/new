import os
from PIL import Image
from app.config import settings


def compress_image(file_path: str) -> dict:
    original_size = os.path.getsize(file_path)
    img = Image.open(file_path)

    if img.mode in ("RGBA", "P"):
        img = img.convert("RGB")

    if max(img.width, img.height) > settings.COMPRESS_MAX_WIDTH:
        ratio = settings.COMPRESS_MAX_WIDTH / max(img.width, img.height)
        img = img.resize(
            (int(img.width * ratio), int(img.height * ratio)), Image.LANCZOS
        )

    img.save(file_path, "JPEG", quality=settings.COMPRESS_QUALITY, optimize=True)
    compressed_size = os.path.getsize(file_path)

    return {
        "original_size": original_size,
        "compressed_size": compressed_size,
        "saved_percent": round((1 - compressed_size / original_size) * 100, 1),
    }
