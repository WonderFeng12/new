from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from pydantic import BaseModel
from app.database import get_db
from app.schemas.contract import ContractCreate, ContractUpdate, ContractOut
from app.services import contract as service
from app.dependencies import get_current_user
from app.models.user import User


class ManualConfirmRequest(BaseModel):
    remark: str

router = APIRouter(prefix="/api/contracts", tags=["contracts"])


@router.get("", response_model=list[ContractOut])
def list_all(
    keyword: str = "",
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    if current_user.role == "生产专员":
        raise HTTPException(status_code=403, detail="权限不足")
    return service.list_contracts(db, keyword, current_user.id, current_user.role)


@router.get("/next-no")
def next_contract_no(
    customer_id: int = None,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    if current_user.role == "生产专员":
        raise HTTPException(status_code=403, detail="权限不足")
    return {"contract_no": service.generate_contract_no(db, customer_id)}


@router.get("/available", response_model=list[ContractOut])
def list_available(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    if current_user.role == "生产专员":
        raise HTTPException(status_code=403, detail="权限不足")
    return service.get_available_contracts(db)


@router.get("/{id}", response_model=ContractOut)
def get_one(
    id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    if current_user.role == "生产专员":
        raise HTTPException(status_code=403, detail="权限不足")
    c = service.get_contract(db, id)
    if not c:
        raise HTTPException(status_code=404, detail="合同不存在")
    return c


@router.post("", response_model=ContractOut)
def create(
    data: ContractCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    if current_user.role == "生产专员":
        raise HTTPException(status_code=403, detail="权限不足")
    return service.create_contract(db, data, current_user.display_name or current_user.username)


@router.put("/{id}", response_model=ContractOut)
def update(
    id: int,
    data: ContractUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    if current_user.role == "生产专员":
        raise HTTPException(status_code=403, detail="权限不足")
    result = service.update_contract(db, id, data, current_user.display_name or current_user.username)
    if not result:
        raise HTTPException(status_code=404, detail="合同不存在")
    return result


@router.delete("/{id}")
def delete(
    id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    if current_user.role == "生产专员":
        raise HTTPException(status_code=403, detail="权限不足")
    if not service.delete_contract(db, id):
        raise HTTPException(status_code=404, detail="合同不存在")
    return {"message": "已删除"}


@router.post("/{id}/manual-confirm", response_model=ContractOut)
def manual_confirm(
    id: int,
    data: ManualConfirmRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    if current_user.role == "生产专员":
        raise HTTPException(status_code=403, detail="权限不足")
    if not data.remark or not data.remark.strip():
        raise HTTPException(status_code=400, detail="确认意见不能为空")
    result = service.manual_confirm_contract(db, id, current_user.id, data.remark.strip())
    if not result:
        raise HTTPException(status_code=404, detail="合同不存在")
    return result
