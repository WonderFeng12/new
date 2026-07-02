import math
from pydantic import BaseModel
from typing import Optional, Any
from datetime import datetime, date
from app.schemas.contract import ContractOut
from app.schemas.spec import SpecOut


class ProcessSheetItemCreate(BaseModel):
    contract_item_id: int
    line_no: int


class ProcessSheetItemOut(BaseModel):
    id: int
    process_sheet_id: int
    contract_item_id: int
    line_no: int
    spec_id: int
    spec: Optional[SpecOut] = None
    is_pressed: bool = False
    packaging_type: Optional[str] = None
    delivery_date: Optional[date] = None
    pattern_count: int = 0
    pattern_data: Optional[Any] = None
    pattern_code: Optional[str] = None
    color_a: Optional[str] = None
    image_a_1: Optional[str] = None
    image_a_2: Optional[str] = None
    image_a_3: Optional[str] = None
    color_b: Optional[str] = None
    image_b_1: Optional[str] = None
    image_b_2: Optional[str] = None
    image_b_3: Optional[str] = None
    pressed_image: Optional[list[str]] = None
    pressed_image_name: Optional[list[str]] = None
    remark: Optional[str] = None
    process_remark: Optional[str] = None
    qty: Optional[float] = 0
    cancel_reason: Optional[str] = None
    cancel_quantities: Optional[dict] = None

    class Config:
        from_attributes = True


class ProcessSheetUpdateItem(BaseModel):
    id: int
    is_pressed: Optional[bool] = None
    packaging_type: Optional[str] = None
    delivery_date: Optional[date] = None
    pattern_count: Optional[int] = None
    pattern_data: Optional[Any] = None
    pattern_code: Optional[str] = None
    color_a: Optional[str] = None
    image_a_1: Optional[str] = None
    image_a_2: Optional[str] = None
    image_a_3: Optional[str] = None
    color_b: Optional[str] = None
    image_b_1: Optional[str] = None
    image_b_2: Optional[str] = None
    image_b_3: Optional[str] = None
    pressed_image: Optional[list[str]] = None
    pressed_image_name: Optional[list[str]] = None
    remark: Optional[str] = None
    qty: Optional[float] = None


class ProcessSheetCreate(BaseModel):
    contract_id: int
    contract_item_ids: list[int]


class MarkVersionRequest(BaseModel):
    note: Optional[str] = None


class ProcessSheetUpdateDetail(BaseModel):
    detail_data: Optional[dict] = None
    items: Optional[list[ProcessSheetUpdateItem]] = None
    change_note: Optional[str] = None


class ProcessSheetOut(BaseModel):
    id: int
    contract_id: int
    sheet_no: str
    confirm_version_no: float = 0
    confirm_image_id: Optional[int] = None
    status: str = "草稿"
    confirm_token: Optional[str] = None
    customer_comment: Optional[str] = None
    customer_confirmed: bool = False
    version_marked: Optional[bool] = False
    version_note: Optional[str] = None
    internal_confirm_required: int = 1
    internal_confirmed_users: Optional[list] = []
    confirm_user_ids: Optional[list] = []
    detail_data: Optional[Any] = None
    contract: Optional[ContractOut] = None
    contract_snapshot: Optional[Any] = None
    created_by: Optional[str] = None
    updated_by: Optional[str] = None
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None
    items: list[ProcessSheetItemOut] = []

    class Config:
        from_attributes = True
