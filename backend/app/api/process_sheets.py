from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from app.database import get_db
from app.schemas.process_sheet import ProcessSheetCreate, ProcessSheetOut
from app.services import process_sheet as service
from app.dependencies import get_current_user
from app.models.user import User

router = APIRouter(prefix="/api/process-sheets", tags=["process-sheets"])


@router.get("", response_model=list[ProcessSheetOut])
def list_all(
    keyword: str = "",
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    return service.list_sheets(db, keyword, current_user.id, current_user.role)


@router.get("/{id}", response_model=ProcessSheetOut)
def get_one(
    id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    s = service.get_sheet(db, id)
    if not s:
        raise HTTPException(status_code=404, detail="工艺单不存在")
    return s


@router.post("", response_model=ProcessSheetOut)
def create(
    data: ProcessSheetCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    return service.create_sheet_from_contract(
        db, data.contract_id, current_user.display_name or current_user.username
    )


@router.post("/push-down/{contract_id}", response_model=ProcessSheetOut)
def push_down(
    contract_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    return service.push_down_from_contract(
        db, contract_id, current_user.display_name or current_user.username
    )


@router.put("/{id}/confirm", response_model=ProcessSheetOut)
def confirm(
    id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    return service.confirm_sheet(db, id, current_user.display_name or current_user.username)


@router.post("/{id}/dispatch", response_model=ProcessSheetOut)
def dispatch(
    id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    return service.dispatch_sheet(db, id, current_user.display_name or current_user.username)


@router.delete("/{id}")
def delete(
    id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    if not service.delete_sheet(db, id):
        raise HTTPException(status_code=404, detail="工艺单不存在")
    return {"message": "已删除"}
