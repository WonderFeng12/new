from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from app.database import get_db
from app.dependencies import require_permission
from app.models.user import User
from app.models.webhook_config import WebhookConfig
from app.schemas.webhook_config import WebhookConfigCreate, WebhookConfigUpdate, WebhookConfigOut

router = APIRouter(prefix="/api/webhook-configs", tags=["webhook-configs"])


@router.get("", response_model=list[WebhookConfigOut])
def list_webhooks(
    db: Session = Depends(get_db),
    current_user: User = Depends(require_permission("settings:webhook:view")),
):
    return db.query(WebhookConfig).order_by(WebhookConfig.id).all()


@router.post("", response_model=WebhookConfigOut)
def create_webhook(
    data: WebhookConfigCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_permission("settings:webhook:manage")),
):
    existing = db.query(WebhookConfig).filter(WebhookConfig.name == data.name).first()
    if existing:
        raise HTTPException(status_code=400, detail="同名webhook已存在")
    wh = WebhookConfig(name=data.name, webhook_url=data.webhook_url, is_enabled=data.is_enabled)
    db.add(wh)
    db.commit()
    db.refresh(wh)
    return wh


@router.put("/{webhook_id}", response_model=WebhookConfigOut)
def update_webhook(
    webhook_id: int,
    data: WebhookConfigUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_permission("settings:webhook:manage")),
):
    wh = db.query(WebhookConfig).filter(WebhookConfig.id == webhook_id).first()
    if not wh:
        raise HTTPException(status_code=404, detail="webhook不存在")
    if data.name is not None:
        wh.name = data.name
    if data.webhook_url is not None:
        wh.webhook_url = data.webhook_url
    if data.is_enabled is not None:
        wh.is_enabled = data.is_enabled
    db.commit()
    db.refresh(wh)
    return wh


@router.delete("/{webhook_id}")
def delete_webhook(
    webhook_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_permission("settings:webhook:manage")),
):
    wh = db.query(WebhookConfig).filter(WebhookConfig.id == webhook_id).first()
    if not wh:
        raise HTTPException(status_code=404, detail="webhook不存在")
    db.delete(wh)
    db.commit()
    return {"message": "已删除"}
