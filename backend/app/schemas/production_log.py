from pydantic import BaseModel
from typing import Optional
from datetime import datetime


class ProductionLogOut(BaseModel):
    id: int
    contract_id: int
    contract_item_id: Optional[int] = None
    process_sheet_id: Optional[int] = None
    from_status: Optional[str] = None
    to_status: str
    operation_type: str
    operator_id: Optional[int] = None
    operator_name: Optional[str] = None
    remark: Optional[str] = None
    created_at: Optional[datetime] = None
    notify_status: str = "pending"

    class Config:
        from_attributes = True
