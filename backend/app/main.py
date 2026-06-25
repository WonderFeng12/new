from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from app.config import settings
from app.api import auth
import os

app = FastAPI(title="花织工厂管理系统", version="1.0.0")

app.include_router(auth.router)

os.makedirs(settings.UPLOAD_DIR, exist_ok=True)
app.mount("/uploads", StaticFiles(directory=settings.UPLOAD_DIR), name="uploads")

@app.get("/api/health")
def health():
    return {"status": "ok"}
