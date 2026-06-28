import json
from sqlalchemy.orm import Session, joinedload
from app.models.contract import Contract
from app.models.contract_item import ContractItem
from sqlalchemy.orm import defaultload
from app.schemas.contract import ContractCreate, ContractUpdate
from app.schemas.contract_item import ContractItemCreate
from fastapi import HTTPException


def _parse_code_rule(value: str) -> dict:
    """Parse code rule value: new JSON format {'suffix':'','customer_id':N} or legacy plain suffix."""
    if not value:
        return {"suffix": ""}
    try:
        return json.loads(value)
    except (json.JSONDecodeError, ValueError):
        return {"suffix": value}


def generate_contract_no(db: Session, customer_id: int = None) -> str:
    if customer_id:
        from app.models.basic_data import BasicData
        rules = db.query(BasicData).filter(
            BasicData.category == "code_rules",
        ).all()
        for rule in rules:
            rule_data = _parse_code_rule(rule.value)
            if rule_data.get("customer_id") == customer_id:
                prefix = rule.code
                suffix = rule_data.get("suffix", "")
                like_pattern = f"{prefix}%{suffix}"
                existing = db.query(Contract).filter(
                    Contract.contract_no.like(like_pattern),
                    Contract.is_deleted == False,
                ).all()
                max_serial = 0
                for c in existing:
                    no = c.contract_no
                    if no.startswith(prefix):
                        mid = no[len(prefix):]
                        if suffix and mid.endswith(suffix):
                            mid = mid[:-len(suffix)]
                        if mid.isdigit():
                            max_serial = max(max_serial, int(mid))
                next_serial = max_serial + 1
                return f"{prefix}{next_serial:03d}{suffix}"

    # Legacy format (no code rule found for this customer)
    last = db.query(Contract).order_by(Contract.id.desc()).first()
    seq = (last.id + 1) if last else 1
    from datetime import date
    today = date.today()
    return f"HT{today.strftime('%Y%m')}{seq:04d}"


def compute_contract_status(db: Session, contract_id: int, items: list = None) -> str:
    """Derive the display-friendly contract status from its items' production_status."""
    if items is None:
        items = db.query(ContractItem).filter(
            ContractItem.contract_id == contract_id
        ).all()
    if not items:
        return "草稿"
    statuses = [i.production_status for i in items]
    has_any = any(s for s in statuses)
    all_cancelled = all(s == "cancelled" for s in statuses if s) and has_any
    all_completed = all(s == "completed" for s in statuses if s) and has_any
    any_production = any(s and s not in ("cancelled", "completed") for s in statuses)

    if all_cancelled:
        return "已取消"
    if all_completed:
        return "已完成"
    if any_production:
        return "已下发"
    if has_any:
        return "确认"
    return "草稿"


def list_contracts(
    db: Session,
    keyword: str = "",
    user_id: int | None = None,
    role: str = "",
):
    q = db.query(Contract).filter(Contract.is_deleted == False)
    if keyword:
        q = q.filter(
            Contract.contract_no.like(f"%{keyword}%")
        )
    if role == "业务员" and user_id:
        from app.models.user import User
        user = db.query(User).filter(User.id == user_id).first()
        if user:
            q = q.filter(Contract.created_by == (user.display_name or user.username))
    contracts = q.order_by(Contract.id.desc()).options(
        joinedload(Contract.customer),
        joinedload(Contract.spec),
        joinedload(Contract.items).joinedload(ContractItem.spec),
    ).all()
    for c in contracts:
        c.computed_status = compute_contract_status(db, c.id, c.items)
    return contracts


def get_contract(db: Session, id: int):
    contract = db.query(Contract).filter(
        Contract.id == id, Contract.is_deleted == False
    ).options(
        joinedload(Contract.customer),
        joinedload(Contract.spec),
        joinedload(Contract.items).joinedload(ContractItem.spec),
    ).first()
    if contract:
        contract.computed_status = compute_contract_status(db, contract.id, contract.items)
    return contract


def create_contract(db: Session, data: ContractCreate, username: str):
    items_data = data.items
    data_dict = data.model_dump(exclude={"items"})
    data_dict["created_by"] = username
    data_dict["updated_by"] = username
    if not data_dict.get("contract_no"):
        data_dict["contract_no"] = generate_contract_no(db)

    contract = Contract(**data_dict)
    db.add(contract)
    db.flush()

    total = 0
    for item_data in items_data:
        item = ContractItem(
            contract_id=contract.id,
            line_no=item_data.line_no,
            spec_id=item_data.spec_id,
            is_pressed=item_data.is_pressed,
            packaging_type=item_data.packaging_type or "",
            delivery_date=item_data.delivery_date,
            pattern_count=item_data.pattern_count or 0,
            pattern_data=item_data.pattern_data,
            unit_price=item_data.unit_price,
            qty=item_data.qty,
            amount=(item_data.unit_price or 0) * (item_data.qty or 0),
            pattern_code=item_data.pattern_code or "",
            color_a=item_data.color_a or "",
            image_a_1=item_data.image_a_1 or "",
            image_a_2=item_data.image_a_2 or "",
            image_a_3=item_data.image_a_3 or "",
            color_b=item_data.color_b or "",
            image_b_1=item_data.image_b_1 or "",
            image_b_2=item_data.image_b_2 or "",
            image_b_3=item_data.image_b_3 or "",
            remark=item_data.remark or "",
        )
        db.add(item)
        total += (item.amount or 0)

    contract.total_amount = total
    db.commit()
    db.refresh(contract)
    return get_contract(db, contract.id)


def update_contract(db: Session, id: int, data: ContractUpdate, username: str):
    contract = get_contract(db, id)
    if not contract:
        return None
    if contract.status == "已下发":
        raise HTTPException(status_code=400, detail="合同已下发，不可修改")
    if contract.is_pushed_down:
        from app.models.process_sheet import ProcessSheet
        sheet = db.query(ProcessSheet).filter(
            ProcessSheet.id == contract.push_down_sheet_id,
            ProcessSheet.is_deleted == False
        ).first()
        if sheet and sheet.status == "已下发":
            raise HTTPException(status_code=400, detail="工艺单已下发，不可修改合同")

    items_data = data.model_dump(exclude_unset=True).pop("items", None)
    for field, value in data.model_dump(exclude_unset=True, exclude={"items"}).items():
        setattr(contract, field, value)

    if items_data is not None:
        from app.schemas.contract_item import ContractItemUpdateWithId
        incoming_ids = set()
        total = 0
        for raw in items_data:
            item_data = raw if isinstance(raw, ContractItemUpdateWithId) else ContractItemUpdateWithId(**raw)
            if item_data.id:
                # Update existing item
                existing = db.query(ContractItem).filter(
                    ContractItem.id == item_data.id,
                    ContractItem.contract_id == id,
                ).first()
                if existing:
                    existing.line_no = item_data.line_no
                    existing.spec_id = item_data.spec_id
                    existing.packaging_type = item_data.packaging_type or ""
                    existing.delivery_date = item_data.delivery_date
                    existing.unit_price = item_data.unit_price
                    existing.qty = item_data.qty
                    existing.amount = (item_data.unit_price or 0) * (item_data.qty or 0)
                    existing.is_pressed = item_data.is_pressed
                    existing.remark = item_data.remark or ""
                    total += (existing.amount or 0)
                    incoming_ids.add(item_data.id)
            else:
                # Insert new item
                item = ContractItem(
                    contract_id=id,
                    line_no=item_data.line_no,
                    spec_id=item_data.spec_id,
                    is_pressed=item_data.is_pressed,
                    packaging_type=item_data.packaging_type or "",
                    delivery_date=item_data.delivery_date,
                    unit_price=item_data.unit_price,
                    qty=item_data.qty,
                    amount=(item_data.unit_price or 0) * (item_data.qty or 0),
                    remark=item_data.remark or "",
                )
                db.add(item)
                db.flush()
                total += (item.amount or 0)
                incoming_ids.add(item.id)

        # Remove items not in the update — skip if referenced by process_sheet_item
        db_items = db.query(ContractItem).filter(
            ContractItem.contract_id == id,
        ).all()
        for existing in db_items:
            if existing.id not in incoming_ids:
                from app.models.process_sheet_item import ProcessSheetItem
                ref = db.query(ProcessSheetItem).filter(
                    ProcessSheetItem.contract_item_id == existing.id
                ).first()
                if ref:
                    # Keep orphaned items that are referenced by process sheets
                    continue
                db.delete(existing)
        contract.total_amount = total

    contract.updated_by = username
    db.commit()
    db.refresh(contract)
    return get_contract(db, contract.id)


def delete_contract(db: Session, id: int):
    contract = db.query(Contract).filter(Contract.id == id).first()
    if not contract:
        return False
    if contract.status != "草稿":
        raise HTTPException(status_code=400, detail="仅草稿状态合同可删除")
    contract.is_deleted = True
    db.commit()
    return True


def manual_confirm_contract(db: Session, contract_id: int, user_id: int, remark: str):
    """管理员手动确认合同，需带确认意见。"""
    from app.models.contract import Contract
    from app.models.production_log import ProductionLog
    from app.models.user import User

    contract = db.query(Contract).filter(
        Contract.id == contract_id, Contract.is_deleted == False
    ).first()
    if not contract:
        raise HTTPException(status_code=404, detail="合同不存在")
    if contract.status == "已下发":
        raise HTTPException(status_code=400, detail="合同已下发，不可确认")
    if contract.status == "确认":
        raise HTTPException(status_code=400, detail="合同已确认")

    user = db.query(User).filter(User.id == user_id).first()
    if not user or (user.role != "销售经理" and user.username != "admin"):
        raise HTTPException(status_code=403, detail="仅管理员可手动确认")

    old_status = contract.status
    contract.status = "确认"
    contract.updated_by = user.display_name or user.username

    log = ProductionLog(
        contract_id=contract.id,
        from_status=old_status,
        to_status="确认",
        operation_type="确认",
        operator_id=user.id,
        remark=f"手动确认: {remark}" if remark else "手动确认",
    )
    db.add(log)
    db.commit()
    db.refresh(contract)
    return contract


def get_available_contracts(db: Session):
    return db.query(Contract).filter(
        Contract.is_deleted == False,
        Contract.status == "确认",
    ).options(
        joinedload(Contract.customer),
        joinedload(Contract.spec),
        joinedload(Contract.items),
    ).all()


