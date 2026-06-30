import logging
from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from app.config import settings
from app.api import auth, customers, specs, contracts, upload, process_sheets, basic_data, public, production, users, webhook_config, permissions
from app.services.reminder import check_contract_reminders
import os

logger = logging.getLogger(__name__)

app = FastAPI(title="嘉元瑞通工厂管理系统", version="1.0.0")

app.include_router(auth.router)
app.include_router(customers.router)
app.include_router(specs.router)
app.include_router(contracts.router)
app.include_router(upload.router)
app.include_router(process_sheets.router)
app.include_router(basic_data.router)
app.include_router(public.router)
app.include_router(production.router)
app.include_router(users.router)
app.include_router(webhook_config.router)
app.include_router(permissions.router)

os.makedirs(settings.UPLOAD_DIR, exist_ok=True)
app.mount("/uploads", StaticFiles(directory=settings.UPLOAD_DIR), name="uploads")


@app.on_event("startup")
def start_scheduler():
    """启动定时催办任务（每天早上8点检查合同确认状态）。"""
    try:
        from apscheduler.schedulers.background import BackgroundScheduler
        scheduler = BackgroundScheduler()
        scheduler.add_job(
            check_contract_reminders,
            trigger="cron",
            hour=8,
            minute=0,
            id="contract_reminder",
            replace_existing=True,
        )
        scheduler.start()
        logger.info("催办定时任务已启动（每天 08:00）")
    except Exception as e:
        logger.warning(f"催办定时任务启动失败（不影响业务）: {e}")


@app.get("/api/health")
def health():
    return {"status": "ok"}
