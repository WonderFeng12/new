from pydantic import BaseModel
from typing import Optional, Any
from datetime import datetime


class ConfirmImageOut(BaseModel):
    id: int
    contract_id: int
    version_no: int
    generated_at: datetime
    generated_by: Optional[str] = None
    change_log: Optional[str] = None
    is_confirmed: bool = False
    confirmed_at: Optional[datetime] = None
    confirmed_by: Optional[str] = None
    image_path: Optional[str] = None

    class Config:
        from_attributes = True


class ConfirmImageFullOut(ConfirmImageOut):
    contract_snapshot: Optional[Any] = None
