from sqlalchemy.orm import Session, joinedload
from fastapi import HTTPException
from app.models.contract import Contract
from app.models.process_sheet import ProcessSheet
from app.models.confirm_image import ConfirmImage


def generate_sheet_no(db: Session) -> str:
    last = db.query(ProcessSheet).order_by(ProcessSheet.id.desc()).first()
    seq = (last.id + 1) if last else 1
    from datetime import date
    today = date.today()
    return f"GY{today.strftime('%Y%m')}{seq:04d}"


def list_sheets(db: Session, keyword: str = "", user_id: int | None = None, role: str = ""):
    q = db.query(ProcessSheet).filter(ProcessSheet.is_deleted == False)
    if keyword:
        q = q.filter(ProcessSheet.sheet_no.like(f"%{keyword}%"))
    if role == "业务员" and user_id:
        from app.models.user import User
        user = db.query(User).filter(User.id == user_id).first()
        if user:
            username = user.display_name or user.username
            q = q.join(Contract).filter(Contract.created_by == username)
    return q.order_by(ProcessSheet.id.desc()).options(
        joinedload(ProcessSheet.contract),
        joinedload(ProcessSheet.confirm_image),
    ).all()


def get_sheet(db: Session, id: int):
    return db.query(ProcessSheet).filter(
        ProcessSheet.id == id, ProcessSheet.is_deleted == False
    ).options(
        joinedload(ProcessSheet.contract),
        joinedload(ProcessSheet.confirm_image),
    ).first()


def push_down_from_contract(db: Session, contract_id: int, username: str):
    contract = db.query(Contract).filter(Contract.id == contract_id).first()
    if not contract or contract.is_deleted:
        raise HTTPException(status_code=404, detail="合同不存在")
    if contract.status != "保存":
        raise HTTPException(status_code=400, detail="合同尚未确认，无法下推")
    if contract.is_pushed_down:
        raise HTTPException(status_code=400, detail="合同已下推，不可重复操作")

    latest_image = db.query(ConfirmImage).filter(
        ConfirmImage.contract_id == contract_id,
        ConfirmImage.version_no == contract.latest_confirm_version,
    ).first()

    sheet_no = generate_sheet_no(db)
    sheet = ProcessSheet(
        contract_id=contract_id,
        sheet_no=sheet_no,
        confirm_version_no=contract.latest_confirm_version,
        confirm_image_id=latest_image.id if latest_image else None,
        status="草稿",
        created_by=username,
        updated_by=username,
    )
    db.add(sheet)
    db.flush()

    contract.is_pushed_down = True
    contract.push_down_sheet_id = sheet.id
    contract.status = "已下发"
    contract.updated_by = username
    db.commit()
    db.refresh(sheet)
    return get_sheet(db, sheet.id)


def confirm_sheet(db: Session, id: int, username: str):
    sheet = get_sheet(db, id)
    if not sheet:
        raise HTTPException(status_code=404, detail="工艺单不存在")
    if sheet.status != "草稿":
        raise HTTPException(status_code=400, detail="工艺单状态不正确")
    sheet.status = "保存"
    sheet.updated_by = username
    db.commit()
    return get_sheet(db, id)


def dispatch_sheet(db: Session, id: int, username: str):
    sheet = get_sheet(db, id)
    if not sheet:
        raise HTTPException(status_code=404, detail="工艺单不存在")
    if sheet.status != "保存":
        raise HTTPException(status_code=400, detail="工艺单未确认，无法下发")

    contract = sheet.contract
    if sheet.confirm_version_no < contract.latest_confirm_version:
        raise HTTPException(
            status_code=400,
            detail=f"合同已有新版本(V{contract.latest_confirm_version})，当前工艺单基于V{sheet.confirm_version_no}，请重新生成工艺单",
        )

    sheet.status = "已下发"
    sheet.updated_by = username
    contract.status = "已下发"
    db.commit()
    return get_sheet(db, id)


def create_sheet_from_contract(db: Session, contract_id: int, username: str):
    """Create process sheet by selecting an available contract (non-push-down)."""
    contract = db.query(Contract).filter(Contract.id == contract_id).first()
    if not contract or contract.is_deleted:
        raise HTTPException(status_code=404, detail="合同不存在")
    if contract.status != "保存":
        raise HTTPException(status_code=400, detail="合同尚未确认")
    if contract.is_pushed_down:
        raise HTTPException(status_code=400, detail="合同已下推")

    return push_down_from_contract(db, contract_id, username)


def delete_sheet(db: Session, id: int):
    sheet = db.query(ProcessSheet).filter(ProcessSheet.id == id).first()
    if not sheet:
        return False
    if sheet.status == "已下发":
        raise HTTPException(status_code=400, detail="工艺单已下发，不可删除")
    sheet.is_deleted = True
    db.commit()
    return True
