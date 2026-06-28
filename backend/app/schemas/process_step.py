from pydantic import BaseModel
from typing import Optional, List
from datetime import datetime


class ProcessStepCreate(BaseModel):
    step_code: str
    step_name: str
    sort_order: int = 0
    is_active: bool = True


class ProcessStepUpdate(BaseModel):
    step_code: Optional[str] = None
    step_name: Optional[str] = None
    sort_order: Optional[int] = None
    is_active: Optional[bool] = None


class ProcessStepOut(BaseModel):
    id: int
    step_code: str
    step_name: str
    sort_order: int
    is_active: bool
    created_at: Optional[datetime] = None

    class Config:
        from_attributes = True


class AssigneeUser(BaseModel):
    id: int
    display_name: str
    role: str
    wecom_userid: Optional[str] = None

    class Config:
        from_attributes = True


class ProcessStepWithAssignees(ProcessStepOut):
    assignees: List[AssigneeUser] = []


class AssigneesUpdate(BaseModel):
    user_ids: List[int]
