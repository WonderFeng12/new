import json
from datetime import date, datetime
from sqlalchemy import or_
from sqlalchemy.orm import Session, joinedload
from app.models.contract import Contract
from app.models.contract_item import ContractItem
from app.models.customer import Customer
from app.models.spec import Spec
from app.models.process_sheet import ProcessSheet
from app.models.process_sheet_item import ProcessSheetItem
from app.schemas.contract import ContractCreate, ContractUpdate
from app.schemas.contract_item import ContractItemCreate
from fastapi import HTTPException
from app.services.production import get_process_sheet_for_item


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


def compute_contract_status(db: Session, contract_id: int, items: list = None, current_status: str = None) -> str:
    """Derive the display-friendly contract status from its items' production_status."""
    if items is None:
        items = db.query(ContractItem).filter(
            ContractItem.contract_id == contract_id
        ).all()
    if not items:
        return current_status or "草稿"
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
    return current_status or "草稿"


def list_contracts(
    db: Session,
    keyword: str = "",
    user_id: int | None = None,
    role: str = "",
):
    q = db.query(Contract).filter(Contract.is_deleted == False)
    if keyword:
        like = f"%{keyword}%"
        q = q.filter(or_(
            Contract.contract_no.like(like),
            Contract.id.in_(
                db.query(ProcessSheet.contract_id).filter(
                    ProcessSheet.is_deleted == False,
                    ProcessSheet.sheet_no.like(like),
                )
            ),
            Contract.id.in_(
                db.query(ContractItem.contract_id).filter(
                    ContractItem.yarn_plan_no.like(like),
                )
            ),
            Contract.id.in_(
                db.query(ContractItem.contract_id).join(Spec).filter(
                    or_(
                        Spec.spec_name.like(like),
                        Spec.spec_description.like(like),
                    )
                )
            ),
            Contract.id.in_(
                db.query(ContractItem.contract_id).filter(
                    ContractItem.packaging_type.like(like),
                )
            ),
            Contract.customer_id.in_(
                db.query(Customer.id).filter(
                    Customer.name.like(like),
                )
            ),
        ))
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
        c.computed_status = compute_contract_status(db, c.id, c.items, c.status)
        _enrich_item_sheets(db, c.items)
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
        contract.computed_status = compute_contract_status(db, contract.id, contract.items, contract.status)
        _enrich_item_sheets(db, contract.items)
    return contract


def _enrich_item_sheets(db: Session, items: list):
    """Populate process sheet info and yarn plan info on contract items."""
    for item in items:
        sheet_info = get_process_sheet_for_item(db, item.id)
        if sheet_info:
            item.has_process_sheet = True
            item.process_sheet_id = sheet_info["id"]
            item.process_sheet_no = sheet_info["sheet_no"]
            item.process_sheet_status = sheet_info["status"]
            item.process_sheet_version = sheet_info.get("confirm_version_no", 0)
        else:
            item.has_process_sheet = False
        if item.yarn_plan_user_id:
            from app.models.user import User
            u = db.query(User).filter(User.id == item.yarn_plan_user_id).first()
            if u:
                item.yarn_plan_user_name = u.display_name


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

    # Add production log for contract creation
    from app.models.production_log import ProductionLog
    log = ProductionLog(
        contract_id=contract.id,
        from_status=None,
        to_status="草稿",
        operation_type="创建",
        operator_id=None,
        remark=f"合同已创建（{contract.contract_no}），共{len(items_data)}个行项目",
    )
    db.add(log)
    db.commit()

    return get_contract(db, contract.id)


def _can_edit_confirmed(db: Session, role: str) -> bool:
    """Check if a role is allowed to edit confirmed contracts."""
    from app.models.basic_data import BasicData
    config = db.query(BasicData).filter(
        BasicData.category == "contract_permissions",
        BasicData.code == "edit_confirmed_roles",
    ).first()
    if not config or not config.value:
        return False
    try:
        allowed = json.loads(config.value)
        return role in allowed
    except (json.JSONDecodeError, TypeError):
        return False


def _build_change_summary(db: Session, contract: Contract, old_data: dict,
                          old_items: list, items_data: list | None) -> str | None:
    """Compare old and new contract data, return a human-readable change summary."""
    from app.models.spec import Spec

    changes = []

    field_labels = {
        "binding_material": "包边材料", "binding_width": "包边宽度",
        "binding_color_no": "色号", "emboss_model": "压花型号",
        "delivery_date": "交货日期",
    }
    for field, label in field_labels.items():
        old_val = old_data.get(field)
        new_val = getattr(contract, field, None)
        if str(old_val or "") != str(new_val or ""):
            changes.append(f"{label}({old_val or '空'}→{new_val or '空'})")

    for i in range(1, 11):
        f = f"tech_note_{i}"
        if str(old_data.get(f, "") or "") != str(getattr(contract, f, "") or ""):
            changes.append(f"技术说明{i}")
    for i in range(1, 6):
        f = f"pack_note_{i}"
        if str(old_data.get(f, "") or "") != str(getattr(contract, f, "") or ""):
            changes.append(f"包装说明{i}")
    for i in range(1, 4):
        f = f"box_note_{i}"
        if str(old_data.get(f, "") or "") != str(getattr(contract, f, "") or ""):
            changes.append(f"箱单说明{i}")

    # Item-level changes
    old_map = {str(it["id"]): it for it in old_items if it["id"]}
    if items_data:
        for new_it in items_data:
            new_id = str(new_it.get("id")) if new_it.get("id") else None
            if new_id and new_id in old_map:
                old_it = old_map[new_id]
                ln = new_it.get("line_no", "?")
                item_changes = []
                if str(old_it.get("packaging_type", "") or "") != str(new_it.get("packaging_type", "") or ""):
                    item_changes.append(f"包装方式({old_it.get('packaging_type') or '空'}→{new_it.get('packaging_type') or '空'})")
                old_qty = float(old_it.get("qty") or 0)
                new_qty = float(new_it.get("qty") or 0)
                if old_qty != new_qty:
                    item_changes.append(f"数量({old_qty}→{new_qty})")
                if bool(old_it.get("is_pressed", False)) != bool(new_it.get("is_pressed", False)):
                    old_p = '是' if old_it.get('is_pressed') else '否'
                    new_p = '是' if new_it.get('is_pressed') else '否'
                    item_changes.append(f"压花({old_p}→{new_p})")
                if str(old_it.get("delivery_date") or "") != str(new_it.get("delivery_date") or ""):
                    item_changes.append("交货日期")
                if old_it.get("spec_id") != new_it.get("spec_id"):
                    old_spec = old_it.get("spec") or db.query(Spec).filter(Spec.id == old_it["spec_id"]).first()
                    new_spec = db.query(Spec).filter(Spec.id == new_it.get("spec_id")).first()
                    item_changes.append(f"规格({old_spec.spec_name if old_spec else '?'}→{new_spec.spec_name if new_spec else '?'})")
                if item_changes:
                    changes.append(f"行项目{ln}# {'，'.join(item_changes)}")
            else:
                changes.append(f"行项目#{new_it.get('line_no', '?')} 新增")

        old_ids = set(it["id"] for it in old_items if it["id"])
        new_ids = set(it.get("id") for it in items_data if it.get("id"))
        for did in old_ids - new_ids:
            dit = next((it for it in old_items if it["id"] == did), None)
            if dit:
                changes.append(f"行项目#{dit['line_no']} 已删除")

    if not changes:
        return None
    summary = "修改了：\n" + "\n".join(changes)
    if len(summary) > 500:
        summary = summary[:497] + "..."
    return summary


def update_contract(db: Session, id: int, data: ContractUpdate, username: str, user_role: str = ""):
    contract = get_contract(db, id)
    if not contract:
        return None
    if contract.status == "已下发":
        if not _can_edit_confirmed(db, user_role):
            raise HTTPException(status_code=400, detail="合同已下发，不可修改")
    if contract.is_pushed_down:
        from app.models.process_sheet import ProcessSheet
        sheet = db.query(ProcessSheet).filter(
            ProcessSheet.id == contract.push_down_sheet_id,
            ProcessSheet.is_deleted == False
        ).first()
        if sheet and sheet.status == "已下发":
            if not _can_edit_confirmed(db, user_role):
                raise HTTPException(status_code=400, detail="工艺单已下发，不可修改合同")

    items_data = data.model_dump(exclude_unset=True).pop("items", None)
    original_status = contract.status

    # Snapshot old values for change summary
    old_data = {
        "binding_material": contract.binding_material,
        "binding_width": contract.binding_width,
        "binding_color_no": contract.binding_color_no,
        "emboss_model": contract.emboss_model,
        "delivery_date": str(contract.delivery_date) if contract.delivery_date else None,
    }
    for i in range(1, 11):
        old_data[f"tech_note_{i}"] = getattr(contract, f"tech_note_{i}", "")
    for i in range(1, 6):
        old_data[f"pack_note_{i}"] = getattr(contract, f"pack_note_{i}", "")
    for i in range(1, 4):
        old_data[f"box_note_{i}"] = getattr(contract, f"box_note_{i}", "")
    old_items = [
        {
            "id": it.id,
            "line_no": it.line_no,
            "spec_id": it.spec_id,
            "packaging_type": it.packaging_type,
            "qty": it.qty,
            "is_pressed": it.is_pressed,
            "delivery_date": str(it.delivery_date) if it.delivery_date else None,
            "spec": db.query(Spec).filter(Spec.id == it.spec_id).first(),
        }
        for it in contract.items
    ]

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

    # Log edits with change summary
    change_summary = _build_change_summary(
        db, contract, old_data, old_items, items_data,
    )
    if change_summary:
        from app.models.production_log import ProductionLog
        log = ProductionLog(
            contract_id=contract.id,
            from_status=original_status,
            to_status=contract.status,
            operation_type="修改",
            operator_id=None,
            remark=change_summary,
        )
        db.add(log)

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
    contract.latest_confirm_version = (contract.latest_confirm_version or 0) + 1

    log = ProductionLog(
        contract_id=contract.id,
        from_status=old_status,
        to_status="确认",
        operation_type="确认",
        operator_id=user.id,
        remark=f"手动确认，版本 V{contract.latest_confirm_version}" + (f"：{remark}" if remark else ""),
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


def reopen_edit(db: Session, contract_id: int, user_id: int):
    """Log that a contract has been reopened for editing. Increments version number."""
    from app.models.production_log import ProductionLog
    from app.models.user import User

    contract = db.query(Contract).filter(
        Contract.id == contract_id, Contract.is_deleted == False
    ).first()
    if not contract:
        raise HTTPException(status_code=404, detail="合同不存在")
    if contract.status == "草稿":
        raise HTTPException(status_code=400, detail="草稿合同可直接编辑，无需重新打开")

    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="用户不存在")
    if user.role not in ("销售经理", "生产专员"):
        raise HTTPException(status_code=403, detail="权限不足")

    original_status = contract.status
    contract.status = "草稿"

    log = ProductionLog(
        contract_id=contract.id,
        from_status=original_status,
        to_status=contract.status,
        operation_type="重新编辑",
        operator_id=user_id,
        remark=f"重新打开编辑（由{user.display_name}操作）",
    )
    db.add(log)
    db.commit()
    return True


def update_confirm_request_time(db: Session, contract_id: int, requested_at):
    """Record when a confirm request was sent (for reminder tracking)."""
    from datetime import datetime
    contract = db.query(Contract).filter(Contract.id == contract_id).first()
    if contract:
        contract.confirm_requested_at = requested_at
        db.commit()


def get_contracts_pending_confirm(db: Session) -> list[dict]:
    """Get all contracts that have been requested for confirm but not yet confirmed.

    Returns list of dicts with contract_no and requested_at for reminder purposes.
    """
    today = date.today()
    contracts = db.query(Contract).filter(
        Contract.is_deleted == False,
        Contract.status == "草稿",
        Contract.confirm_requested_at.isnot(None),
    ).all()

    result = []
    for c in contracts:
        # Only include if not already reminded today
        if c.last_reminded_at and c.last_reminded_at.date() == today:
            continue
        result.append({
            "contract_no": c.contract_no,
            "requested_at": c.confirm_requested_at.strftime("%Y-%m-%d %H:%M") if c.confirm_requested_at else "",
        })
    return result


def mark_reminded(db: Session, contract_no: str):
    """Mark a contract as having been reminded today."""
    from datetime import datetime
    contract = db.query(Contract).filter(
        Contract.contract_no == contract_no
    ).first()
    if contract:
        contract.last_reminded_at = datetime.now()
        db.commit()