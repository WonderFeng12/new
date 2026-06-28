from pydantic import BaseModel
from typing import Optional, Any
from datetime import date


class ContractItemCreate(BaseModel):
    spec_id: int
    line_no: int
    is_pressed: Optional[bool] = False
    packaging_type: Optional[str] = ""
    delivery_date: Optional[date] = None
    pattern_count: Optional[int] = 0
    pattern_data: Optional[list[dict[str, Any]]] = None
    unit_price: Optional[float] = None
    qty: Optional[float] = None
    pattern_code: Optional[str] = ""
    color_a: Optional[str] = ""
    image_a_1: Optional[str] = ""
    image_a_2: Optional[str] = ""
    image_a_3: Optional[str] = ""
    color_b: Optional[str] = ""
    image_b_1: Optional[str] = ""
    image_b_2: Optional[str] = ""
    image_b_3: Optional[str] = ""
    remark: Optional[str] = ""


class ContractItemUpdate(BaseModel):
    spec_id: Optional[int] = None
    line_no: Optional[int] = None
    is_pressed: Optional[bool] = None
    packaging_type: Optional[str] = None
    delivery_date: Optional[date] = None
    pattern_count: Optional[int] = None
    pattern_data: Optional[list[dict[str, Any]]] = None
    unit_price: Optional[float] = None
    qty: Optional[float] = None
    pattern_code: Optional[str] = None
    color_a: Optional[str] = None
    image_a_1: Optional[str] = None
    image_a_2: Optional[str] = None
    image_a_3: Optional[str] = None
    color_b: Optional[str] = None
    image_b_1: Optional[str] = None
    image_b_2: Optional[str] = None
    image_b_3: Optional[str] = None
    remark: Optional[str] = None


class ContractItemOut(BaseModel):
    id: int
    contract_id: int
    spec_id: Optional[int] = None
    line_no: int
    is_pressed: Optional[bool] = False
    packaging_type: Optional[str] = ""
    delivery_date: Optional[date] = None
    pattern_count: Optional[int] = 0
    pattern_data: Optional[Any] = None
    unit_price: Optional[float] = None
    qty: Optional[float] = None
    amount: Optional[float] = None
    pattern_code: Optional[str] = ""
    color_a: Optional[str] = ""
    image_a_1: Optional[str] = ""
    image_a_2: Optional[str] = ""
    image_a_3: Optional[str] = ""
    color_b: Optional[str] = ""
    image_b_1: Optional[str] = ""
    image_b_2: Optional[str] = ""
    image_b_3: Optional[str] = ""
    remark: Optional[str] = ""
    spec_description: Optional[str] = None
    production_status: Optional[str] = None
    yarn_plan_user_id: Optional[int] = None
    cancel_quantities: Optional[Any] = None
    cancel_reason: Optional[str] = None
    yarn_plan_user_name: Optional[str] = None

    class Config:
        from_attributes = True
