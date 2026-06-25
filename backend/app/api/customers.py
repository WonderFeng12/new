from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from app.database import get_db
from app.schemas.customer import CustomerCreate, CustomerUpdate, CustomerOut
from app.services import customer as service
from app.dependencies import get_current_user
from app.models.user import User

router = APIRouter(prefix="/api/customers", tags=["customers"])

@router.get("", response_model=list[CustomerOut])
def list_all(keyword: str = "", db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    return service.list_customers(db, keyword)

@router.get("/{id}", response_model=CustomerOut)
def get_one(id: int, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    c = service.get_customer(db, id)
    if not c:
        raise HTTPException(status_code=404, detail="客户不存在")
    return c

@router.post("", response_model=CustomerOut)
def create(data: CustomerCreate, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    return service.create_customer(db, data, current_user.display_name or current_user.username)

@router.put("/{id}", response_model=CustomerOut)
def update(id: int, data: CustomerUpdate, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    result = service.update_customer(db, id, data, current_user.display_name or current_user.username)
    if not result:
        raise HTTPException(status_code=404, detail="客户不存在")
    return result

@router.delete("/{id}")
def delete(id: int, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    if not service.delete_customer(db, id):
        raise HTTPException(status_code=404, detail="客户不存在")
    return {"message": "已删除"}
