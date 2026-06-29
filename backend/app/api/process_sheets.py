from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import Response
from sqlalchemy.orm import Session
from app.database import get_db
from app.schemas.process_sheet import (
    ProcessSheetCreate, ProcessSheetOut, ProcessSheetUpdateDetail, MarkVersionRequest
)
from app.schemas.production_log import ProductionLogOut
from app.services import process_sheet as service
from app.utils.pdf_generator import render_process_sheet, HAS_WEASYPRINT
from app.dependencies import get_current_user, require_role
from app.models.user import User
from app.models.production_log import ProductionLog

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
    if current_user.role == "业务员":
        raise HTTPException(status_code=403, detail="权限不足")
    return service.create_sheet_from_items(
        db, data.contract_id, data.contract_item_ids,
        current_user.display_name or current_user.username
    )


@router.put("/{id}/detail", response_model=ProcessSheetOut)
def update_detail(
    id: int,
    data: ProcessSheetUpdateDetail,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    if current_user.role == "业务员":
        raise HTTPException(status_code=403, detail="权限不足")
    items_data = [i.model_dump(exclude_unset=True) for i in data.items] if data.items else None
    return service.update_sheet_detail(
        db, id, data.detail_data, items_data,
        current_user.display_name or current_user.username,
        change_note=data.change_note,
    )


@router.post("/{id}/mark-version", response_model=ProcessSheetOut)
def mark_version(
    id: int,
    data: MarkVersionRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    return service.mark_version(
        db, id, data.note,
        current_user.display_name or current_user.username,
    )


@router.put("/{id}/confirm", response_model=ProcessSheetOut)
def confirm(
    id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    return service.confirm_sheet(db, id, current_user.display_name or current_user.username)


@router.post("/{id}/internal-confirm", response_model=ProcessSheetOut)
def internal_confirm(
    id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    if current_user.role not in ("销售经理", "生产专员"):
        raise HTTPException(status_code=403, detail="权限不足")
    return service.internal_confirm_sheet(db, id, current_user)


@router.post("/{id}/reopen-edit", response_model=ProcessSheetOut)
def reopen_edit(
    id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    if current_user.role not in ("销售经理", "生产专员"):
        raise HTTPException(status_code=403, detail="权限不足")
    return service.reopen_sheet_edit(db, id, current_user)


@router.put("/{id}/confirm-requirements", response_model=ProcessSheetOut)
def set_confirm_reqs(
    id: int,
    required_count: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    if current_user.role != "销售经理":
        raise HTTPException(status_code=403, detail="权限不足")
    return service.set_confirm_requirements(db, id, required_count, current_user)


@router.post("/{id}/dispatch", response_model=ProcessSheetOut)
def dispatch(
    id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    return service.dispatch_sheet(db, id, current_user.display_name or current_user.username)


@router.get("/{id}/print")
def print_sheet(
    id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_role("销售经理", "生产专员")),
):
    sheet = service.get_sheet(db, id)
    if not sheet:
        raise HTTPException(status_code=404, detail="工艺单不存在")
    pdf_bytes = render_process_sheet(sheet, sheet.contract, sheet.items)
    return Response(
        content=pdf_bytes,
        media_type="application/pdf",
        headers={"Content-Disposition": f'attachment; filename="{sheet.sheet_no}.pdf"'},
    )


@router.delete("/{id}")
def delete(
    id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    if not service.delete_sheet(db, id):
        raise HTTPException(status_code=404, detail="工艺单不存在")
    return {"message": "已删除"}


@router.get("/{id}/logs", response_model=list[ProductionLogOut])
def get_sheet_logs(
    id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    logs = db.query(ProductionLog).filter(
        ProductionLog.process_sheet_id == id,
    ).order_by(ProductionLog.created_at.desc()).all()
    # Attach operator name
    from app.models.user import User as UserModel
    for log in logs:
        if log.operator_id:
            u = db.query(UserModel).filter(UserModel.id == log.operator_id).first()
            log.operator_name = u.display_name if u else None
        else:
            log.operator_name = None
    return logs


@router.put("/{id}/confirm-users", response_model=ProcessSheetOut)
def set_confirm_users(
    id: int,
    user_ids: list[int],
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    if current_user.role != "销售经理":
        raise HTTPException(status_code=403, detail="权限不足")
    return service.set_confirm_users(db, id, user_ids, current_user)


@router.post("/{id}/generate-confirm-link")
def generate_sheet_confirm_link(
    id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    if current_user.role == "生产专员":
        raise HTTPException(status_code=403, detail="权限不足")
    return service.generate_confirm_link(db, id)
