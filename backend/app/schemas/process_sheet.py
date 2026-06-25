from pydantic import BaseModel
from typing import Optional
from datetime import datetime


class ProcessSheetCreate(BaseModel):
    contract_id: int


class ProcessSheetOut(BaseModel):
    id: int
    contract_id: int
    sheet_no: str
    confirm_version_no: int
    confirm_image_id: Optional[int] = None
    status: str = "草稿"
    created_by: Optional[str] = None
    updated_by: Optional[str] = None
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None

    class Config:
        from_attributes = True
