from pydantic import BaseModel
from typing import Optional
from datetime import datetime


class WebhookConfigCreate(BaseModel):
    name: str
    webhook_url: str
    is_enabled: bool = True


class WebhookConfigUpdate(BaseModel):
    name: Optional[str] = None
    webhook_url: Optional[str] = None
    is_enabled: Optional[bool] = None


class WebhookConfigOut(BaseModel):
    id: int
    name: str
    webhook_url: str
    is_enabled: bool
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None

    class Config:
        from_attributes = True
