from pydantic import BaseModel
from typing import Optional
from datetime import datetime

class SpecCreate(BaseModel):
    length: str
    width: str
    weight: str
    layer_type: str

class SpecUpdate(BaseModel):
    length: Optional[str] = None
    width: Optional[str] = None
    weight: Optional[str] = None
    layer_type: Optional[str] = None

class SpecOut(BaseModel):
    id: int
    length: str
    width: str
    weight: str
    layer_type: str
    spec_name: str
    spec_description: Optional[str] = ""
    created_by: Optional[str] = None
    updated_by: Optional[str] = None

    class Config:
        from_attributes = True
