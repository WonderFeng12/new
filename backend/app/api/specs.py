from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from app.database import get_db
from app.schemas.spec import SpecCreate, SpecUpdate, SpecOut
from app.services import spec as service
from app.dependencies import get_current_user
from app.models.user import User

router = APIRouter(prefix="/api/specs", tags=["specs"])

@router.get("", response_model=list[SpecOut])
def list_all(keyword: str = "", db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    return service.list_specs(db, keyword)

@router.get("/{id}", response_model=SpecOut)
def get_one(id: int, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    s = service.get_spec(db, id)
    if not s: raise HTTPException(404, "规格不存在")
    return s

@router.post("", response_model=SpecOut)
def create(data: SpecCreate, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    return service.create_spec(db, data, current_user.display_name or current_user.username)

@router.put("/{id}", response_model=SpecOut)
def update(id: int, data: SpecUpdate, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    result = service.update_spec(db, id, data, current_user.display_name or current_user.username)
    if not result: raise HTTPException(404, "规格不存在")
    return result

@router.delete("/{id}")
def delete(id: int, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    if not service.delete_spec(db, id): raise HTTPException(404, "规格不存在")
    return {"message": "已删除"}
