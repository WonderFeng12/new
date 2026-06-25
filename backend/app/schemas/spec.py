from pydantic import BaseModel
from typing import Optional
from datetime import datetime

class SpecCreate(BaseModel):
    spec_name: str
    weight: str
    layer_type: str
    splice_method: Optional[str] = ""

class SpecUpdate(BaseModel):
    spec_name: Optional[str] = None
    weight: Optional[str] = None
    layer_type: Optional[str] = None
    splice_method: Optional[str] = None

class SpecOut(BaseModel):
    id: int
    spec_name: str
    weight: str
    layer_type: str
    splice_method: Optional[str] = ""
    spec_description: Optional[str] = ""
    created_by: Optional[str] = None
    updated_by: Optional[str] = None

    class Config:
        from_attributes = True
