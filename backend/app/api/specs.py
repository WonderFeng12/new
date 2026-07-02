from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from app.database import get_db
from app.schemas.spec import SpecCreate, SpecUpdate, SpecOut
from app.services import spec as service
from app.dependencies import get_current_user, require_permission
from app.models.user import User

router = APIRouter(prefix="/api/specs", tags=["specs"])

@router.get("", response_model=list[SpecOut])
def list_all(keyword: str = "", db: Session = Depends(get_db), current_user: User = Depends(require_permission("basic_data:view"))):
    return service.list_specs(db, keyword)

@router.get("/{id}", response_model=SpecOut)
def get_one(id: int, db: Session = Depends(get_db), current_user: User = Depends(require_permission("basic_data:view"))):
    s = service.get_spec(db, id)
    if not s: raise HTTPException(404, "规格不存在")
    return s

@router.post("", response_model=SpecOut)
def create(data: SpecCreate, db: Session = Depends(get_db), current_user: User = Depends(require_permission("spec:manage"))):
    return service.create_spec(db, data, current_user.display_name or current_user.username)

@router.put("/{id}", response_model=SpecOut)
def update(id: int, data: SpecUpdate, cascade: bool = False, db: Session = Depends(get_db), current_user: User = Depends(require_permission("spec:manage"))):
    result = service.update_spec(db, id, data, current_user.display_name or current_user.username, cascade=cascade)
    if not result: raise HTTPException(404, "规格不存在")
    return result

@router.post("/{id}/clone", response_model=SpecOut)
def clone(id: int, db: Session = Depends(get_db), current_user: User = Depends(require_permission("spec:manage"))):
    return service.clone_spec(db, id, current_user.display_name or current_user.username)

@router.delete("/{id}")
def delete(id: int, db: Session = Depends(get_db), current_user: User = Depends(require_permission("spec:manage"))):
    if not service.delete_spec(db, id): raise HTTPException(404, "规格不存在")
    return {"message": "已删除"}
