import json
import uuid
from sqlalchemy.orm import Session, joinedload
from fastapi import HTTPException
from app.models.contract import Contract
from app.models.process_sheet import ProcessSheet
from app.models.process_sheet_item import ProcessSheetItem
from app.models.confirm_image import ConfirmImage


def generate_sheet_no(db: Session) -> str:
    from datetime import date
    today = date.today()
    month = today.month

    like_pattern = f"{month}-%"
    existing = db.query(ProcessSheet).filter(
        ProcessSheet.sheet_no.like(like_pattern),
        ProcessSheet.is_deleted == False,
    ).all()

    max_serial = 0
    for s in existing:
        parts = s.sheet_no.split("-")
        if len(parts) == 2 and parts[0] == str(month) and parts[1].isdigit():
            max_serial = max(max_serial, int(parts[1]))

    next_serial = max_serial + 1
    return f"{month}-{next_serial}"


def _load_items(sheet):
    """Eagerly load items on a process sheet."""
    if sheet:
        sheet.items
    return sheet


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
        joinedload(ProcessSheet.items),
    ).all()


def get_sheet(db: Session, id: int):
    return db.query(ProcessSheet).filter(
        ProcessSheet.id == id, ProcessSheet.is_deleted == False
    ).options(
        joinedload(ProcessSheet.contract),
        joinedload(ProcessSheet.confirm_image),
        joinedload(ProcessSheet.items),
    ).first()


def create_sheet_from_items(db: Session, contract_id: int, contract_item_ids: list[int], username: str):
    """Create process sheet from selected contract items (no push-down side effects)."""
    contract = db.query(Contract).filter(Contract.id == contract_id).first()
    if not contract or contract.is_deleted:
        raise HTTPException(status_code=404, detail="合同不存在")
    if contract.status != "保存":
        raise HTTPException(status_code=400, detail="合同尚未确认")

    sheet_no = generate_sheet_no(db)
    sheet = ProcessSheet(
        contract_id=contract_id,
        sheet_no=sheet_no,
        confirm_version_no=contract.latest_confirm_version,
        status="草稿",
        created_by=username,
        updated_by=username,
    )
    db.add(sheet)
    db.flush()

    # Create ProcessSheetItems for selected contract items
    from app.models.contract_item import ContractItem
    items = db.query(ContractItem).filter(
        ContractItem.id.in_(contract_item_ids),
        ContractItem.contract_id == contract_id,
    ).all()

    existing_ids = set(i.id for i in items)
    for cid in contract_item_ids:
        if cid not in existing_ids:
            raise HTTPException(status_code=400, detail=f"合同行项目 {cid} 不存在或不属于该合同")

    for idx, ci in enumerate(items):
        psi = ProcessSheetItem(
            process_sheet_id=sheet.id,
            contract_item_id=ci.id,
            line_no=idx + 1,
            spec_id=ci.spec_id,
            packaging_type=ci.packaging_type or '',
        )
        db.add(psi)

    db.commit()
    db.refresh(sheet)
    return get_sheet(db, sheet.id)


def update_sheet_detail(db: Session, id: int, detail_data: dict | None, items_data: list | None, username: str):
    """Update process sheet detail data and item-level production details."""
    sheet = get_sheet(db, id)
    if not sheet:
        raise HTTPException(status_code=404, detail="工艺单不存在")
    if sheet.status != "草稿":
        raise HTTPException(status_code=400, detail="工艺单已确认或已下发，不可修改")

    if detail_data is not None:
        sheet.detail_data = detail_data

    if items_data is not None:
        for item_data in items_data:
            psi = db.query(ProcessSheetItem).filter(
                ProcessSheetItem.id == item_data.get("id"),
                ProcessSheetItem.process_sheet_id == id,
            ).first()
            if not psi:
                continue
            for field, value in item_data.items():
                if field == "id":
                    continue
                if hasattr(psi, field):
                    setattr(psi, field, value)

    sheet.updated_by = username
    db.commit()
    db.refresh(sheet)
    return get_sheet(db, sheet.id)


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

    # Create ProcessSheetItems for ALL contract items
    from app.models.contract_item import ContractItem
    all_items = db.query(ContractItem).filter(
        ContractItem.contract_id == contract_id,
    ).order_by(ContractItem.line_no).all()
    for idx, ci in enumerate(all_items):
        psi = ProcessSheetItem(
            process_sheet_id=sheet.id,
            contract_item_id=ci.id,
            line_no=idx + 1,
            spec_id=ci.spec_id,
            packaging_type=ci.packaging_type or '',
        )
        db.add(psi)

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
    if sheet.status not in ("保存", "已确认"):
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


def generate_confirm_link(db: Session, sheet_id: int) -> dict:
    """Generate a public confirm link for a process sheet."""
    sheet = db.query(ProcessSheet).filter(
        ProcessSheet.id == sheet_id, ProcessSheet.is_deleted == False
    ).first()
    if not sheet:
        raise HTTPException(status_code=404, detail="工艺单不存在")
    if not sheet.confirm_token:
        sheet.confirm_token = str(uuid.uuid4())
        db.commit()
        db.refresh(sheet)
    url = f"/api/public/process-sheet/{sheet.confirm_token}"
    return {"token": sheet.confirm_token, "url": url}


def customer_confirm_sheet(db: Session, token: str, comment: str = "") -> dict:
    """Customer confirms a process sheet via public link."""
    from app.models.production_log import ProductionLog

    sheet = db.query(ProcessSheet).filter(
        ProcessSheet.confirm_token == token, ProcessSheet.is_deleted == False
    ).first()
    if not sheet:
        raise HTTPException(status_code=404, detail="确认链接无效")
    if sheet.status == "已确认":
        return {"already_confirmed": True, "message": "该工艺单已被确认"}

    old_status = sheet.status
    sheet.customer_comment = comment or ""
    sheet.status = "已确认"

    log = ProductionLog(
        contract_id=sheet.contract_id,
        from_status=old_status,
        to_status="已确认",
        operation_type="确认",
        operator_id=None,  # customer, no user account
        remark=f"客户确认: {comment}" if comment else "客户确认",
    )
    db.add(log)
    db.commit()
    return {"already_confirmed": False, "message": "确认成功"}
