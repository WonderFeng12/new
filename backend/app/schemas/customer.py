from pydantic import BaseModel
from typing import Optional
from datetime import datetime

class CustomerCreate(BaseModel):
    name: str
    contact: Optional[str] = ""
    phone: Optional[str] = ""
    address: Optional[str] = ""

class CustomerUpdate(BaseModel):
    name: Optional[str] = None
    contact: Optional[str] = None
    phone: Optional[str] = None
    address: Optional[str] = None

class CustomerOut(BaseModel):
    id: int
    customer_no: str
    name: str
    contact: Optional[str] = ""
    phone: Optional[str] = ""
    address: Optional[str] = ""
    is_in_use: bool = False
    created_by: Optional[str] = None
    updated_by: Optional[str] = None
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None

    class Config:
        from_attributes = True
