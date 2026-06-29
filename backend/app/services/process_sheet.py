import json
import math
import uuid
from sqlalchemy.orm import Session, joinedload, selectinload
from fastapi import HTTPException
from app.models.contract import Contract
from app.models.process_sheet import ProcessSheet
from app.models.process_sheet_item import ProcessSheetItem


def format_version_str(v):
    """Format version number for display: 0→'V0', 0.11→'V0.11', 1→'V1'."""
    if v is None or v == 0:
        return "V0"
    num = float(v)
    if num % 1 == 0:
        return f"V{int(num)}"
    return f"V{num:.2f}"


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
        selectinload(ProcessSheet.items).joinedload(ProcessSheetItem.spec),
    ).all()


def get_sheet(db: Session, id: int):
    return db.query(ProcessSheet).filter(
        ProcessSheet.id == id, ProcessSheet.is_deleted == False
    ).options(
        joinedload(ProcessSheet.contract),
        selectinload(ProcessSheet.items).joinedload(ProcessSheetItem.spec),
    ).first()


def create_sheet_from_items(db: Session, contract_id: int, contract_item_ids: list[int], username: str):
    """Create process sheet from selected contract items (no push-down side effects)."""
    contract = db.query(Contract).filter(Contract.id == contract_id).first()
    if not contract or contract.is_deleted:
        raise HTTPException(status_code=404, detail="合同不存在")
    if contract.status != "确认":
        raise HTTPException(status_code=400, detail="合同尚未确认")

    sheet_no = generate_sheet_no(db)
    # Inherit default confirm users from system config
    from app.models.system_config import SystemConfig
    config = db.query(SystemConfig).filter(
        SystemConfig.config_key == "process_sheet_confirm_users"
    ).first()
    default_confirm_users = []
    if config and config.config_value:
        try:
            import json
            default_confirm_users = json.loads(config.config_value)
        except (json.JSONDecodeError, TypeError):
            default_confirm_users = []

    sheet = ProcessSheet(
        contract_id=contract_id,
        sheet_no=sheet_no,
        confirm_version_no=0,  # 工艺单独立版本体系，初始 V0
        status="草稿",
        confirm_user_ids=default_confirm_users,
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


def _build_sheet_change_summary(detail_data: dict, old_detail: dict,
                                 items_data: list | None, old_items: list) -> str | None:
    """Compare old and new process sheet data, return a human-readable change summary."""
    changes = []

    # detail_data field comparison
    detail_labels = {
        "binding_material": "包边材料", "binding_width": "包边宽度",
        "binding_color_no": "色号", "emboss_model": "压花型号",
        "tolerance": "公差",
    }
    for field, label in detail_labels.items():
        old_val = old_detail.get(field, "")
        new_val = detail_data.get(field, "") if detail_data else old_val
        if str(old_val or "") != str(new_val or ""):
            changes.append(f"{label}({old_val or '空'}→{new_val or '空'})")

    for i in range(1, 11):
        f = f"tech_note_{i}"
        if str(old_detail.get(f, "") or "") != str((detail_data or {}).get(f, "") or ""):
            changes.append(f"技术说明{i}")
    for i in range(1, 6):
        f = f"pack_note_{i}"
        if str(old_detail.get(f, "") or "") != str((detail_data or {}).get(f, "") or ""):
            changes.append(f"包装说明{i}")
    for i in range(1, 4):
        f = f"box_note_{i}"
        if str(old_detail.get(f, "") or "") != str((detail_data or {}).get(f, "") or ""):
            changes.append(f"箱单说明{i}")
    for i in range(1, 4):
        f = f"accessory_desc_{i}"
        if str(old_detail.get(f, "") or "") != str((detail_data or {}).get(f, "") or ""):
            changes.append(f"辅料{i}")
    for i in range(1, 4):
        f = f"accessory_size_{i}"
        if str(old_detail.get(f, "") or "") != str((detail_data or {}).get(f, "") or ""):
            changes.append(f"辅料{i}尺寸")
    for i in range(1, 4):
        f = f"accessory_qty_{i}"
        if str(old_detail.get(f, "") or "") != str((detail_data or {}).get(f, "") or ""):
            changes.append(f"辅料{i}数量")

    # Item-level changes
    if items_data and old_items:
        old_map = {str(it.id): it for it in old_items}
        for new_it in items_data:
            new_id = str(new_it.get("id")) if new_it.get("id") else None
            if new_id and new_id in old_map:
                old_it = old_map[new_id]
                ln = new_it.get("line_no", "?")
                item_changes = []
                if str(getattr(old_it, "packaging_type", "") or "") != str(new_it.get("packaging_type", "") or ""):
                    item_changes.append(f"包装方式({getattr(old_it, 'packaging_type') or '空'}→{new_it.get('packaging_type') or '空'})")
                old_qty = float(getattr(old_it, "qty", 0) or 0)
                new_qty = float(new_it.get("qty", 0) or 0)
                if old_qty != new_qty:
                    item_changes.append(f"数量({old_qty}→{new_qty})")
                if bool(getattr(old_it, "is_pressed", False)) != bool(new_it.get("is_pressed", False)):
                    old_p = '是' if getattr(old_it, 'is_pressed') else '否'
                    new_p = '是' if new_it.get('is_pressed') else '否'
                    item_changes.append(f"压花({old_p}→{new_p})")
                if str(getattr(old_it, "delivery_date", "") or "") != str(new_it.get("delivery_date", "") or ""):
                    item_changes.append("交期")
                old_pc = getattr(old_it, "pattern_count", 0) or 0
                new_pc = new_it.get("pattern_count", 0) or 0
                if old_pc != new_pc:
                    item_changes.append(f"花型数({old_pc}→{new_pc})")
                if new_it.get("pressed_image") and getattr(old_it, "pressed_image", "") != new_it["pressed_image"]:
                    item_changes.append("压花图片")
                if item_changes:
                    changes.append(f"行{ln}# {'，'.join(item_changes)}")

    if not changes:
        return None
    summary = "修改了：\n" + "\n".join(changes)
    if len(summary) > 500:
        summary = summary[:497] + "..."
    return summary


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

    # Capture old data for change comparison
    old_detail = dict(sheet.detail_data or {})
    old_items = list(db.query(ProcessSheetItem).filter(
        ProcessSheetItem.process_sheet_id == id
    ).all())

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
    new_v = current_v
    if current_v > 0:
        new_v = current_v + 0.01
        sheet.confirm_version_no = new_v
    sheet.updated_by = username

    # Build change summary
    change_summary = _build_sheet_change_summary(
        detail_data, old_detail, items_data, old_items
    )

    # Log the save operation
    from app.models.production_log import ProductionLog
    remark_parts = ["工艺详情已保存"]
    if new_v > 0:
        remark_parts.append(f"版本 {format_version_str(new_v)}")
    if change_note:
        remark_parts.append(f"({change_note})")
    if change_summary:
        remark_parts.append(f"\n{change_summary}")
    remark = "，".join(remark_parts)

    log = ProductionLog(
        contract_id=sheet.contract_id,
        process_sheet_id=sheet.id,
        from_status=sheet.status,
        to_status=sheet.status,
        operation_type="修改",
        operator_id=None,
        remark=remark,
    )
    db.add(log)
    db.commit()
    db.refresh(sheet)
    return get_sheet(db, sheet.id)


def mark_version(db: Session, id: int, note: str | None, username: str):
    """Mark current version for customer communication. Each click increments version by 0.01."""
    sheet = get_sheet(db, id)
    if not sheet:
        raise HTTPException(status_code=404, detail="工艺单不存在")
    if sheet.status != "草稿":
        raise HTTPException(status_code=400, detail="工艺单已确认或已下发")

    # Increment version on each communication click
    current_v = float(sheet.confirm_version_no or 0)
    if current_v == 0:
        sheet.confirm_version_no = 0.11
    else:
        sheet.confirm_version_no = current_v + 0.01

    sheet.version_marked = True
    sheet.version_note = note or ""
    sheet.updated_by = username

    from app.models.production_log import ProductionLog
    log = ProductionLog(
        contract_id=sheet.contract_id,
        process_sheet_id=sheet.id,
        from_status="草稿",
        to_status="草稿",
        operation_type="修改",
        operator_id=None,
        remark=f"客户沟通标记，版本 {format_version_str(sheet.confirm_version_no)}" + (f"：{note}" if note else ""),
    )
    db.add(log)
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

    from app.models.production_log import ProductionLog
    log = ProductionLog(
        contract_id=sheet.contract_id,
        process_sheet_id=sheet.id,
        from_status="草稿",
        to_status="保存",
        operation_type="确认",
        operator_id=None,
        remark=f"客户确认，正式版本 {format_version_str(sheet.confirm_version_no)}",
    )
    db.add(log)
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

    from app.models.production_log import ProductionLog
    log = ProductionLog(
        contract_id=sheet.contract_id,
        process_sheet_id=sheet.id,
        from_status="保存",
        to_status="已下发",
        operation_type="确认",
        operator_id=None,
        remark="工艺单已下发至车间",
    )
    db.add(log)
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
    """Customer confirms a process sheet via public link.
    Sets version to V0.5 and marks customer_confirmed=True, then awaits internal confirmations."""
    from app.models.production_log import ProductionLog
    from app.services.notify import send_message
    from app.models.user import User as UserModel

    sheet = db.query(ProcessSheet).filter(
        ProcessSheet.confirm_token == token, ProcessSheet.is_deleted == False
    ).first()
    if not sheet:
        raise HTTPException(status_code=404, detail="确认链接无效")
    if sheet.customer_confirmed:
        return {"already_confirmed": True, "message": "该工艺单已被确认"}

    old_status = sheet.status
    sheet.customer_comment = comment or ""
    sheet.customer_confirmed = True
    sheet.version_marked = False

    # Set version to 0.5 if lower
    current_v = float(sheet.confirm_version_no or 0)
    if current_v < 0.5:
        sheet.confirm_version_no = 0.5

    log = ProductionLog(
        contract_id=sheet.contract_id,
        process_sheet_id=sheet.id,
        from_status=old_status,
        to_status=old_status,
        operation_type="确认",
        operator_id=None,
        remark=f"客户确认，版本 {format_version_str(sheet.confirm_version_no)}" + (f"：{comment}" if comment else ""),
    )
    db.add(log)

    # Notify designated confirm users via WeCom
    confirm_ids = list(sheet.confirm_user_ids or [])
    mentioned_list = []
    if confirm_ids:
        users = db.query(UserModel).filter(
            UserModel.id.in_(confirm_ids),
            UserModel.is_active == True,
        ).all()
        mentioned_list = [u.wecom_userid for u in users if u.wecom_userid]

    if mentioned_list:
        sheet_no = sheet.sheet_no
        send_message(
            db,
            f"工艺单 {sheet_no} 客户已确认，请登录系统进行内部确认\n",
            mentioned_list=mentioned_list,
            webhook_type="工艺单通知",
        )

    db.commit()
    return {"already_confirmed": False, "message": "确认成功"}


def internal_confirm_sheet(db: Session, id: int, user) -> dict:
    """Internal multi-person confirmation. Only users in confirm_user_ids can confirm."""
    from app.models.production_log import ProductionLog
    from app.services.notify import send_message

    sheet = get_sheet(db, id)
    if not sheet:
        raise HTTPException(status_code=404, detail="工艺单不存在")
    if not sheet.customer_confirmed:
        raise HTTPException(status_code=400, detail="客户尚未确认，请先等待客户确认")
    if sheet.status != "草稿":
        raise HTTPException(status_code=400, detail="工艺单状态不正确")

    # Check if user is in the confirm user list
    confirm_ids = list(sheet.confirm_user_ids or [])
    if confirm_ids and user.id not in confirm_ids:
        raise HTTPException(status_code=403, detail="您不是本工艺单指定的确认人，无法确认")

    # Add current user to confirmed list if not already there
    confirmed = list(sheet.internal_confirmed_users or [])
    if user.id not in confirmed:
        confirmed.append(user.id)
        sheet.internal_confirmed_users = confirmed

    # Determine if all required users have confirmed
    if confirm_ids:
        all_confirmed = all(uid in confirmed for uid in confirm_ids)
    else:
        # Fallback to internal_confirm_required for backward compatibility
        required = sheet.internal_confirm_required or 1
        all_confirmed = len(confirmed) >= required
    current_count = len(confirmed)

    log_remark = f"内部确认：{user.display_name or user.username}（{current_count}/{required}）"
    if all_confirmed:
        # Upgrade version to next integer
        current_v = float(sheet.confirm_version_no or 0)
        if current_v < 1:
            new_v = 1.0
        else:
            new_v = math.floor(current_v) + 1.0
        sheet.confirm_version_no = new_v
        sheet.version_marked = False
        sheet.status = "保存"
        sheet.updated_by = user.display_name or user.username
        log_remark += f"，全部确认完成，正式版本 {format_version_str(new_v)}"

        # Send WeCom notification: complete
        send_message(
            db,
            f"工艺单 {sheet.sheet_no} 已完成内部确认，版本 {format_version_str(new_v)}",
            mentioned_list=[],
            webhook_type="工艺单通知",
        )
    else:
        # Send WeCom notification: progress
        send_message(
            db,
            f"{user.display_name or user.username} 已确认工艺单 {sheet.sheet_no}（{current_count}/{required}）",
            mentioned_list=[],
            webhook_type="工艺单通知",
        )

    log = ProductionLog(
        contract_id=sheet.contract_id,
        process_sheet_id=sheet.id,
        from_status="草稿",
        to_status="保存" if all_confirmed else "草稿",
        operation_type="确认",
        operator_id=user.id,
        remark=log_remark,
    )
    db.add(log)
    db.commit()
    db.refresh(sheet)
    return get_sheet(db, sheet.id)


def reopen_sheet_edit(db: Session, id: int, user) -> dict:
    """Reopen editing after customer/internal confirmation. Like contract reopen, resets status and bumps version."""
    from app.models.production_log import ProductionLog

    sheet = get_sheet(db, id)
    if not sheet:
        raise HTTPException(status_code=404, detail="工艺单不存在")
    if sheet.status == "已下发":
        raise HTTPException(status_code=400, detail="工艺单已下发，不可重新编辑")
    if not sheet.customer_confirmed and sheet.status == "草稿":
        raise HTTPException(status_code=400, detail="客户尚未确认，无需重新编辑")

    old_status = sheet.status

    # 回到草稿，重置客户确认状态，版本号保持不变（与合同逻辑一致）
    sheet.status = "草稿"
    sheet.customer_confirmed = False
    sheet.internal_confirmed_users = []
    sheet.updated_by = user.display_name or user.username

    log_remark = "重新打开编辑"

    log = ProductionLog(
        contract_id=sheet.contract_id,
        process_sheet_id=sheet.id,
        from_status=old_status,
        to_status="草稿",
        operation_type="重新编辑",
        operator_id=user.id,
        remark=log_remark,
    )
    db.add(log)
    db.commit()
    db.refresh(sheet)
    return get_sheet(db, sheet.id)


def set_confirm_requirements(db: Session, id: int, required_count: int, user) -> dict:
    """Set how many internal confirmations are needed (sales manager only)."""
    sheet = get_sheet(db, id)
    if not sheet:
        raise HTTPException(status_code=404, detail="工艺单不存在")
    if required_count < 1:
        raise HTTPException(status_code=400, detail="确认人数至少为 1")

    sheet.internal_confirm_required = required_count
    sheet.updated_by = user.display_name or user.username
    db.commit()
    db.refresh(sheet)
    return get_sheet(db, sheet.id)


def set_confirm_users(db: Session, id: int, user_ids: list[int], user) -> dict:
    """Set the list of designated confirm users for a process sheet."""
    sheet = get_sheet(db, id)
    if not sheet:
        raise HTTPException(status_code=404, detail="工艺单不存在")

    # Validate user IDs exist
    from app.models.user import User as UserModel
    found = db.query(UserModel).filter(
        UserModel.id.in_(user_ids),
        UserModel.is_active == True,
    ).count()
    if found != len(user_ids):
        raise HTTPException(status_code=400, detail="部分用户ID无效或已被禁用")

    sheet.confirm_user_ids = user_ids
    sheet.updated_by = user.display_name or user.username
    db.commit()
    db.refresh(sheet)
    return get_sheet(db, sheet.id)
