import json
import requests
from sqlalchemy.orm import Session
from app.models.system_config import SystemConfig
from app.models.production_log import ProductionLog


def _get_webhook_url(db: Session) -> str | None:
    """Get configured WeCom bot webhook URL."""
    config = db.query(SystemConfig).filter(
        SystemConfig.config_key == "wecom_webhook_url"
    ).first()
    return config.config_value if config and config.config_value else None


def _is_notify_enabled(db: Session) -> bool:
    config = db.query(SystemConfig).filter(
        SystemConfig.config_key == "production_notify_enabled"
    ).first()
    return config and config.config_value == "true"


def send_notification(db: Session, log: ProductionLog, message: str):
    """Send a WeCom group bot notification. Failures are non-blocking."""
    if not _is_notify_enabled(db):
        return
    webhook = _get_webhook_url(db)
    if not webhook:
        return

    try:
        payload = {
            "msgtype": "text",
            "text": {
                "content": message,
            }
        }
        resp = requests.post(webhook, json=payload, timeout=5)
        if resp.status_code == 200:
            log.notify_status = "sent"
        else:
            log.notify_status = "failed"
    except Exception:
        log.notify_status = "failed"
