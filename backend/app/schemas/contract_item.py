from pydantic import BaseModel
from typing import Optional


class ContractItemCreate(BaseModel):
    line_no: int
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
    line_no: Optional[int] = None
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
    line_no: int
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

    class Config:
        from_attributes = True
