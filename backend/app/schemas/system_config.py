from pydantic import BaseModel
from typing import Optional


class SystemConfigUpdate(BaseModel):
    config_value: Optional[str] = None


class SystemConfigOut(BaseModel):
    config_key: str
    config_value: Optional[str] = None

    class Config:
        from_attributes = True
