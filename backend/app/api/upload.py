import os
import uuid
from fastapi import APIRouter, UploadFile, File, Depends, HTTPException
from app.config import settings
from app.utils.image_compress import compress_image
from app.dependencies import get_current_user
from app.models.user import User

router = APIRouter(prefix="/api/upload", tags=["upload"])

ALLOWED_EXTS = {".jpg", ".jpeg", ".png", ".bmp"}


@router.post("/images")
async def upload_images(
    files: list[UploadFile] = File(...),
    current_user: User = Depends(get_current_user),
):
    results = []
    for file in files:
        ext = os.path.splitext(file.filename)[1].lower()
        if ext not in ALLOWED_EXTS:
            raise HTTPException(status_code=400, detail=f"不支持的文件格式: {ext}")

        save_name = f"{uuid.uuid4().hex}{ext}"
        save_path = os.path.join(settings.UPLOAD_DIR, save_name)

        content = await file.read()
        with open(save_path, "wb") as f:
            f.write(content)

        compress_info = compress_image(save_path)

        results.append({
            "original_name": file.filename,
            "url": f"/uploads/{save_name}",
            "path": save_name,
            **compress_info,
        })

    return results
