from pydantic import BaseModel
from typing import Optional
from datetime import datetime


class BasicDataCreate(BaseModel):
    category: str = ""
    code: str
    value: Optional[str] = ""
    sort_order: Optional[int] = 0


class BasicDataUpdate(BaseModel):
    code: Optional[str] = None
    value: Optional[str] = None
    sort_order: Optional[int] = None


class BasicDataOut(BaseModel):
    id: int
    category: str
    code: str
    value: Optional[str] = ""
    sort_order: int

    class Config:
        from_attributes = True
