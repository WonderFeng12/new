import json
import math
import uuid
from sqlalchemy.orm import Session, joinedload
from fastapi import HTTPException
from app.models.contract import Contract
from app.models.process_sheet import ProcessSheet
from app.models.process_sheet_item import ProcessSheetItem


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
        joinedload(ProcessSheet.items),
    ).all()


def get_sheet(db: Session, id: int):
    return db.query(ProcessSheet).filter(
        ProcessSheet.id == id, ProcessSheet.is_deleted == False
    ).options(
        joinedload(ProcessSheet.contract),
        joinedload(ProcessSheet.items),
    ).first()


def create_sheet_from_items(db: Session, contract_id: int, contract_item_ids: list[int], username: str):
    """Create process sheet from selected contract items (no push-down side effects)."""
    contract = db.query(Contract).filter(Contract.id == contract_id).first()
    if not contract or contract.is_deleted:
        raise HTTPException(status_code=404, detail="合同不存在")
    if contract.status != "确认":
        raise HTTPException(status_code=400, detail="合同尚未确认")

    sheet_no = generate_sheet_no(db)
    sheet = ProcessSheet(
        contract_id=contract_id,
        sheet_no=sheet_no,
        confirm_version_no=contract.latest_confirm_version or 0,
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


def update_sheet_detail(db: Session, id: int, detail_data: dict | None, items_data: list | None, username: str, change_note: str | None = None):
    """Update process sheet detail data and item-level production details."""
    sheet = get_sheet(db, id)
    if not sheet:
        raise HTTPException(status_code=404, detail="工艺单不存在")
    if sheet.status != "草稿":
        raise HTTPException(status_code=400, detail="工艺单已确认或已下发，不可修改")

    # If version is marked, change reason is required
    if sheet.version_marked and not change_note:
        raise HTTPException(status_code=400, detail="版本已标记用于客户沟通，每次更改请填写原因")

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

    # Auto-increment version by 0.01 if version tracking has started
    current_v = float(sheet.confirm_version_no or 0)
    if current_v > 0:
        sheet.confirm_version_no = current_v + 0.01
    sheet.updated_by = username
    db.commit()
    db.refresh(sheet)
    return get_sheet(db, sheet.id)


def mark_version(db: Session, id: int, note: str | None, username: str):
    """Mark current version for customer communication. First time generates V0.11."""
    sheet = get_sheet(db, id)
    if not sheet:
        raise HTTPException(status_code=404, detail="工艺单不存在")
    if sheet.status != "草稿":
        raise HTTPException(status_code=400, detail="工艺单已确认或已下发")

    # First time: generate initial communication version V0.11
    current_v = float(sheet.confirm_version_no or 0)
    if current_v == 0:
        sheet.confirm_version_no = 0.11

    sheet.version_marked = True
    sheet.version_note = note or ""
    sheet.updated_by = username
    db.commit()
    db.refresh(sheet)
    return get_sheet(db, sheet.id)


def confirm_sheet(db: Session, id: int, username: str):
    sheet = get_sheet(db, id)
    if not sheet:
        raise HTTPException(status_code=404, detail="工艺单不存在")
    if sheet.status != "草稿":
        raise HTTPException(status_code=400, detail="工艺单状态不正确")

    # V0.xx → V1, V1.x → V2, V2.x → V3 …
    current = float(sheet.confirm_version_no or 0)
    if current <= 0:
        sheet.confirm_version_no = 1.0
    else:
        sheet.confirm_version_no = math.floor(current) + 1.0
    sheet.version_marked = False
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
    # Use contract_snapshot to determine the contract version at push-down time
    snap = sheet.contract_snapshot or {}
    if isinstance(snap, str):
        import json
        try:
            snap = json.loads(snap)
        except (json.JSONDecodeError, TypeError):
            snap = {}
    base_version = snap.get("latest_confirm_version", 0) or 0
    if base_version < (contract.latest_confirm_version or 0):
        raise HTTPException(
            status_code=400,
            detail=f"合同已有新版本(V{contract.latest_confirm_version})，当前工艺单基于V{base_version}，请重新生成工艺单",
        )

    sheet.status = "已下发"
    sheet.updated_by = username
    contract.status = "已下发"
    db.commit()
    return get_sheet(db, id)


def delete_sheet(db: Session, id: int):
    sheet = db.query(ProcessSheet).filter(ProcessSheet.id == id).first()
    if not sheet:
        return False
    if sheet.status == "已下发":
        raise HTTPException(status_code=400, detail="工艺单已下发，不可删除")

    contract_id = sheet.contract_id

    # Delete associated process sheet items
    db.query(ProcessSheetItem).filter(
        ProcessSheetItem.process_sheet_id == id
    ).delete()

    # Reset contract push-down state
    contract = db.query(Contract).filter(Contract.id == contract_id).first()
    if contract:
        if contract.push_down_sheet_id == id:
            contract.is_pushed_down = False
            contract.push_down_sheet_id = None
        # Revert status if no remaining process sheets
        remaining = db.query(ProcessSheet).filter(
            ProcessSheet.contract_id == contract_id,
            ProcessSheet.is_deleted == False,
            ProcessSheet.id != id,  # the one being deleted
        ).count()
        if remaining == 0 and contract.status == "已下发":
            contract.status = "确认"

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
