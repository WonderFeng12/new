from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from app.config import settings
from app.api import auth, customers, specs, contracts, upload, process_sheets
import os

app = FastAPI(title="花织工厂管理系统", version="1.0.0")

app.include_router(auth.router)
app.include_router(customers.router)
app.include_router(specs.router)
app.include_router(contracts.router)
app.include_router(upload.router)
app.include_router(process_sheets.router)

os.makedirs(settings.UPLOAD_DIR, exist_ok=True)
app.mount("/uploads", StaticFiles(directory=settings.UPLOAD_DIR), name="uploads")

@app.get("/api/health")
def health():
    return {"status": "ok"}
