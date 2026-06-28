from pydantic import BaseModel
from typing import Optional
from datetime import date, datetime

from app.schemas.contract_item import ContractItemCreate, ContractItemUpdate, ContractItemUpdateWithId, ContractItemOut
from app.schemas.customer import CustomerOut


class ContractCreate(BaseModel):
    contract_no: str
    customer_id: int
    contract_date: date
    spec_id: Optional[int] = None
    spec_description: Optional[str] = ""
    is_pressed: Optional[bool] = False
    packaging_type: Optional[str] = ""
    delivery_date: Optional[date] = None
    binding_material: str = ""
    binding_width: Optional[str] = ""
    binding_color_no: Optional[str] = ""

    tech_note_1: Optional[str] = ""
    tech_note_2: Optional[str] = ""
    tech_note_3: Optional[str] = ""
    tech_note_4: Optional[str] = ""
    tech_note_5: Optional[str] = ""
    tech_note_6: Optional[str] = ""
    tech_note_7: Optional[str] = ""
    tech_note_8: Optional[str] = ""
    tech_note_9: Optional[str] = ""
    tech_note_10: Optional[str] = ""

    accessory_desc_1: Optional[str] = ""
    accessory_size_1: Optional[str] = ""
    accessory_qty_1: Optional[float] = None
    accessory_images_1: Optional[list[str]] = None
    accessory_desc_2: Optional[str] = ""
    accessory_size_2: Optional[str] = ""
    accessory_qty_2: Optional[str] = None
    accessory_images_2: Optional[list[str]] = None
    accessory_desc_3: Optional[str] = ""
    accessory_size_3: Optional[str] = ""
    accessory_qty_3: Optional[str] = None
    accessory_images_3: Optional[list[str]] = None
    accessory_desc_4: Optional[str] = ""
    accessory_size_4: Optional[str] = ""
    accessory_qty_4: Optional[str] = None
    accessory_images_4: Optional[list[str]] = None
    washing_labels: Optional[list[dict]] = None
    origin_labels: Optional[list[dict]] = None
    accessory_desc_5: Optional[str] = ""
    accessory_size_5: Optional[str] = ""
    accessory_qty_5: Optional[float] = None
    accessory_desc_6: Optional[str] = ""
    accessory_size_6: Optional[str] = ""
    accessory_qty_6: Optional[float] = None

    pack_note_1: Optional[str] = ""
    pack_note_2: Optional[str] = ""
    pack_note_3: Optional[str] = ""
    pack_note_4: Optional[str] = ""
    pack_note_5: Optional[str] = ""

    box_note_1: Optional[str] = ""
    box_note_2: Optional[str] = ""
    box_note_3: Optional[str] = ""

    emboss_model: Optional[str] = ""
    items: list[ContractItemCreate] = []


class ContractUpdate(BaseModel):
    contract_no: Optional[str] = None
    customer_id: Optional[int] = None
    contract_date: Optional[date] = None
    spec_id: Optional[int] = None
    spec_description: Optional[str] = None
    is_pressed: Optional[bool] = None
    packaging_type: Optional[str] = None
    delivery_date: Optional[date] = None
    binding_material: Optional[str] = None
    binding_width: Optional[str] = None
    binding_color_no: Optional[str] = None

    tech_note_1: Optional[str] = None
    tech_note_2: Optional[str] = None
    tech_note_3: Optional[str] = None
    tech_note_4: Optional[str] = None
    tech_note_5: Optional[str] = None
    tech_note_6: Optional[str] = None
    tech_note_7: Optional[str] = None
    tech_note_8: Optional[str] = None
    tech_note_9: Optional[str] = None
    tech_note_10: Optional[str] = None

    accessory_desc_1: Optional[str] = None
    accessory_size_1: Optional[str] = None
    accessory_qty_1: Optional[float] = None
    accessory_images_1: Optional[list[str]] = None
    accessory_desc_2: Optional[str] = None
    accessory_size_2: Optional[str] = None
    accessory_qty_2: Optional[str] = None
    accessory_images_2: Optional[list[str]] = None
    accessory_desc_3: Optional[str] = None
    accessory_size_3: Optional[str] = None
    accessory_qty_3: Optional[str] = None
    accessory_images_3: Optional[list[str]] = None
    accessory_desc_4: Optional[str] = None
    accessory_size_4: Optional[str] = None
    accessory_qty_4: Optional[str] = None
    accessory_images_4: Optional[list[str]] = None
    washing_labels: Optional[list[dict]] = None
    origin_labels: Optional[list[dict]] = None
    accessory_desc_5: Optional[str] = None
    accessory_size_5: Optional[str] = None
    accessory_qty_5: Optional[float] = None
    accessory_desc_6: Optional[str] = None
    accessory_size_6: Optional[str] = None
    accessory_qty_6: Optional[float] = None

    pack_note_1: Optional[str] = None
    pack_note_2: Optional[str] = None
    pack_note_3: Optional[str] = None
    pack_note_4: Optional[str] = None
    pack_note_5: Optional[str] = None

    box_note_1: Optional[str] = None
    box_note_2: Optional[str] = None
    box_note_3: Optional[str] = None

    emboss_model: Optional[str] = None
    items: Optional[list[ContractItemUpdateWithId]] = None


class ContractOut(BaseModel):
    id: int
    contract_no: str
    customer_id: int
    customer: Optional[CustomerOut] = None
    contract_date: date
    spec_id: Optional[int] = None
    spec_description: Optional[str] = ""
    is_pressed: Optional[bool] = False
    packaging_type: Optional[str] = ""
    delivery_date: Optional[date] = None
    binding_material: str = ""
    binding_width: Optional[str] = ""
    binding_color_no: Optional[str] = ""
    emboss_model: Optional[str] = ""
    total_amount: Optional[float] = None
    status: str = "草稿"
    is_pushed_down: bool = False
    push_down_sheet_id: Optional[int] = None
    tech_note_1: Optional[str] = ""
    tech_note_2: Optional[str] = ""
    tech_note_3: Optional[str] = ""
    tech_note_4: Optional[str] = ""
    tech_note_5: Optional[str] = ""
    tech_note_6: Optional[str] = ""
    tech_note_7: Optional[str] = ""
    tech_note_8: Optional[str] = ""
    tech_note_9: Optional[str] = ""
    tech_note_10: Optional[str] = ""

    accessory_desc_1: Optional[str] = ""
    accessory_size_1: Optional[str] = ""
    accessory_qty_1: Optional[float] = None
    accessory_desc_2: Optional[str] = ""
    accessory_size_2: Optional[str] = ""
    accessory_qty_2: Optional[str] = None
    accessory_desc_3: Optional[str] = ""
    accessory_size_3: Optional[str] = ""
    accessory_qty_3: Optional[str] = None
    accessory_desc_4: Optional[str] = ""
    accessory_size_4: Optional[str] = ""
    accessory_qty_4: Optional[str] = None
    accessory_images_1: Optional[list[str]] = None
    accessory_images_2: Optional[list[str]] = None
    accessory_images_3: Optional[list[str]] = None
    accessory_images_4: Optional[list[str]] = None
    washing_labels: Optional[list[dict]] = None
    origin_labels: Optional[list[dict]] = None
    accessory_desc_5: Optional[str] = ""
    accessory_size_5: Optional[str] = ""
    accessory_qty_5: Optional[float] = None
    accessory_desc_6: Optional[str] = ""
    accessory_size_6: Optional[str] = ""
    accessory_qty_6: Optional[float] = None

    pack_note_1: Optional[str] = ""
    pack_note_2: Optional[str] = ""
    pack_note_3: Optional[str] = ""
    pack_note_4: Optional[str] = ""
    pack_note_5: Optional[str] = ""

    box_note_1: Optional[str] = ""
    box_note_2: Optional[str] = ""
    box_note_3: Optional[str] = ""

    items: list[ContractItemOut] = []
    created_by: Optional[str] = None
    updated_by: Optional[str] = None
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None
    computed_status: Optional[str] = None

    class Config:
        from_attributes = True
