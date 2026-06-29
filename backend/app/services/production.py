import json
import logging
from datetime import datetime
from sqlalchemy.orm import Session, joinedload
from fastapi import HTTPException
from app.models.contract import Contract
from app.models.contract_item import ContractItem
from app.models.production_log import ProductionLog
from app.models.process_sheet import ProcessSheet
from app.models.process_sheet_item import ProcessSheetItem
from app.models.process_step import ProcessStep
from app.models.user import User
from app.services.process_step import get_ordered_step_codes
from app.services.notify import (
    notify_yarn_plan_released,
    notify_production_advance,
    notify_item_cancelled,
    notify_completed,
)

logger = logging.getLogger(__name__)


def _get_next_step(current: str, ordered_steps: list[str]) -> str | None:
    """Return the step code after current in the ordered list."""
    try:
        idx = ordered_steps.index(current)
        if idx + 1 < len(ordered_steps):
            return ordered_steps[idx + 1]
        return None
    except ValueError:
        return None


def _get_previous_step(current: str, ordered_steps: list[str]) -> str | None:
    """Return the step code before current in the ordered list."""
    try:
        idx = ordered_steps.index(current)
        if idx > 0:
            return ordered_steps[idx - 1]
        return None
    except ValueError:
        return None


def _verify_operator_for_step(db: Session, step_code: str, user_id: int) -> bool:
    """Check if user is an assignee for the given step."""
    from app.models.process_step_assignee import ProcessStepAssignee
    from app.models.process_step import ProcessStep
    step = db.query(ProcessStep).filter(
        ProcessStep.step_code == step_code
    ).first()
    if not step:
        return False
    assignee = db.query(ProcessStepAssignee).filter(
        ProcessStepAssignee.process_step_id == step.id,
        ProcessStepAssignee.user_id == user_id,
    ).first()
    return assignee is not None


def advance_item(db: Session, item_id: int, user_id: int, remark: str = ""):
    """Advance a contract item to the next production step."""
    item = db.query(ContractItem).filter(
        ContractItem.id == item_id
    ).options(joinedload(ContractItem.contract)).first()
    if not item or item.contract.is_deleted:
        raise HTTPException(status_code=404, detail="行项目不存在")

    if item.cancel_reason:
        raise HTTPException(status_code=400, detail="该行项目已取消，无法推进")

    ordered = get_ordered_step_codes(db)
    current = item.production_status

    if not current:
        raise HTTPException(status_code=400, detail="请先下达坯布计划")

    next_step = _get_next_step(current, ordered)
    if not next_step:
        raise HTTPException(status_code=400, detail="该行项目已完成所有工序")

    # Verify operator is assignee of the NEXT step (only they can advance into it)
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="用户不存在")

    has_permission = _verify_operator_for_step(db, next_step, user_id)
    # External yarn_plan_user can advance from weaving
    if current == 'weaving' and item.yarn_plan_user_id == user_id:
        has_permission = True

    if not has_permission and user.role not in ('销售经理', '生产专员'):
        raise HTTPException(status_code=403, detail="你不是下一工序的负责人")

    old_status = item.production_status
    item.production_status = next_step
    db.flush()

    log = ProductionLog(
        contract_id=item.contract_id,
        contract_item_id=item.id,
        from_status=old_status,
        to_status=next_step,
        operation_type="推进",
        operator_id=user_id,
        remark=remark,
    )
    db.add(log)
    db.commit()
    db.refresh(item)

    # Non-blocking WeCom notifications
    try:
        from app.models.process_step import ProcessStep
        from app.models.process_step_assignee import ProcessStepAssignee

        old_step_obj = db.query(ProcessStep).filter(
            ProcessStep.step_code == old_status
        ).first()
        new_step_obj = db.query(ProcessStep).filter(
            ProcessStep.step_code == next_step
        ).first()
        from_step_name = old_step_obj.step_name if old_step_obj else old_status
        to_step_name = new_step_obj.step_name if new_step_obj else next_step

        next_assignees = []
        if new_step_obj:
            assignees = db.query(ProcessStepAssignee).filter(
                ProcessStepAssignee.process_step_id == new_step_obj.id
            ).all()
            next_assignees = [a.user.wecom_userid for a in assignees
                             if a.user and a.user.wecom_userid]

        notify_production_advance(
            db, item.contract.contract_no,
            item.spec_description or "",
            from_step_name, to_step_name,
            user.display_name,
            next_assignees if next_assignees else None,
        )

        # Check if this is the terminal step
        if _get_next_step(next_step, ordered) is None:
            notify_completed(
                db, item.contract.contract_no,
                item.spec_description or "",
            )
    except Exception as e:
        logger.warning(f"通知发送失败（不影响业务）: {e}")

    return item, log


def rollback_item(db: Session, item_id: int, user_id: int, remark: str = ""):
    """Roll back one step (for error correction)."""
    item = db.query(ContractItem).filter(
        ContractItem.id == item_id
    ).options(joinedload(ContractItem.contract)).first()
    if not item or item.contract.is_deleted:
        raise HTTPException(status_code=404, detail="行项目不存在")

    user = db.query(User).filter(User.id == user_id).first()
    if user.role not in ('销售经理', '生产专员'):
        raise HTTPException(status_code=403, detail="权限不足")

    ordered = get_ordered_step_codes(db)
    current = item.production_status
    prev_step = _get_previous_step(current, ordered)
    if not prev_step:
        raise HTTPException(status_code=400, detail="已是最初状态，无法回退")

    old_status = item.production_status
    item.production_status = prev_step
    db.flush()

    log = ProductionLog(
        contract_id=item.contract_id,
        contract_item_id=item.id,
        from_status=old_status,
        to_status=prev_step,
        operation_type="回退",
        operator_id=user_id,
        remark=remark,
    )
    db.add(log)
    db.commit()
    db.refresh(item)
    return item, log


def rework_item(db: Session, item_id: int, target_step: str, user_id: int, remark: str = ""):
    """Rework — return to a specified earlier step."""
    item = db.query(ContractItem).filter(
        ContractItem.id == item_id
    ).options(joinedload(ContractItem.contract)).first()
    if not item or item.contract.is_deleted:
        raise HTTPException(status_code=404, detail="行项目不存在")

    user = db.query(User).filter(User.id == user_id).first()
    if user.role not in ('销售经理', '生产专员'):
        raise HTTPException(status_code=403, detail="权限不足")

    ordered = get_ordered_step_codes(db)
    if target_step not in ordered or target_step == item.production_status:
        raise HTTPException(status_code=400, detail="无效的目标工序")

    current_idx = ordered.index(item.production_status) if item.production_status else -1
    target_idx = ordered.index(target_step)
    if target_idx >= current_idx:
        raise HTTPException(status_code=400, detail="只能返回到当前工序之前的工序")

    old_status = item.production_status
    item.production_status = target_step
    db.flush()

    log = ProductionLog(
        contract_id=item.contract_id,
        contract_item_id=item.id,
        from_status=old_status,
        to_status=target_step,
        operation_type="返工",
        operator_id=user_id,
        remark=remark,
    )
    db.add(log)
    db.commit()
    return item, log


def cancel_item(
    db: Session,
    item_id: int,
    user_id: int,
    reason: str,
    quantities: dict | None = None,
):
    """Cancel a contract item at any stage."""
    item = db.query(ContractItem).filter(
        ContractItem.id == item_id
    ).options(joinedload(ContractItem.contract)).first()
    if not item or item.contract.is_deleted:
        raise HTTPException(status_code=404, detail="行项目不存在")

    user = db.query(User).filter(User.id == user_id).first()
    if user.role not in ('业务员', '销售经理', '生产专员'):
        raise HTTPException(status_code=403, detail="权限不足")
    # 业务员 can only cancel their own contracts
    if user.role == '业务员':
        contract = db.query(Contract).filter(Contract.id == item.contract_id).first()
        if contract and contract.created_by != user.display_name:
            raise HTTPException(status_code=403, detail="只能取消自己创建的合同的行项目")

    old_status = item.production_status
    item.production_status = "cancelled"
    item.cancel_reason = reason
    # Save snapshot for restore capability
    snapshot = dict(quantities or {})
    snapshot.update({
        "contract_version": item.contract.latest_confirm_version,
        "contract_status": item.contract.status,
        "production_status": old_status,
        "detail": reason,
        "restored": False,
    })
    item.cancel_quantities = snapshot
    db.flush()

    log = ProductionLog(
        contract_id=item.contract_id,
        contract_item_id=item.id,
        from_status=old_status,
        to_status="cancelled",
        operation_type="取消",
        operator_id=user_id,
        remark=reason,
    )
    db.add(log)
    db.commit()
    db.refresh(item)

    # Non-blocking WeCom notification
    try:
        notify_item_cancelled(
            db, item.contract.contract_no,
            item.spec_description or "",
            reason,
            user.display_name,
        )
    except Exception as e:
        logger.warning(f"通知发送失败（不影响业务）: {e}")

    return item, log


def restore_item(db: Session, item_id: int, user_id: int):
    """Restore a cancelled contract item to its pre-cancel state."""
    item = db.query(ContractItem).options(
        joinedload(ContractItem.contract)
    ).filter(ContractItem.id == item_id).first()
    if not item or item.contract.is_deleted:
        raise HTTPException(status_code=404, detail="行项目不存在")

    snapshot = item.cancel_quantities
    if not snapshot or snapshot.get("restored"):
        raise HTTPException(status_code=400, detail="无可恢复的取消记录")

    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="用户不存在")

    # Restore production status
    item.production_status = snapshot.get("production_status")
    item.cancel_reason = None
    snapshot["restored"] = True
    item.cancel_quantities = snapshot

    log = ProductionLog(
        contract_id=item.contract_id,
        contract_item_id=item.id,
        from_status="cancelled",
        to_status=snapshot.get("production_status"),
        operation_type="取消",
        operator_id=user_id,
        remark="已恢复取消：行项目恢复到取消前状态",
    )
    db.add(log)
    db.commit()
    db.refresh(item)
    return item, log


def release_yarn_plan(
    db: Session,
    item_id: int,
    user_id: int,
    yarn_plan_user_id: int,
    remark: str = "",
):
    """Release yarn plan and assign the external collaborator."""
    item = db.query(ContractItem).filter(
        ContractItem.id == item_id
    ).options(joinedload(ContractItem.contract)).first()
    if not item or item.contract.is_deleted:
        raise HTTPException(status_code=404, detail="行项目不存在")

    if item.production_status is not None:
        raise HTTPException(status_code=400, detail="坯布计划已下达")

    user = db.query(User).filter(User.id == user_id).first()
    if user.role not in ('销售经理', '生产专员'):
        raise HTTPException(status_code=403, detail="权限不足")

    yarn_user = db.query(User).filter(User.id == yarn_plan_user_id).first()
    if not yarn_user:
        raise HTTPException(status_code=404, detail="指定的坯布负责人不存在")

    item.production_status = "yarn_plan"
    item.yarn_plan_user_id = yarn_plan_user_id
    if not item.yarn_plan_no:
        from datetime import date
        today = date.today()
        count = db.query(ContractItem).filter(
            ContractItem.yarn_plan_no.isnot(None)
        ).count()
        item.yarn_plan_no = f"YP{today.strftime('%Y%m')}{count + 1:04d}"
    db.flush()

    log = ProductionLog(
        contract_id=item.contract_id,
        contract_item_id=item.id,
        from_status=None,
        to_status="yarn_plan",
        operation_type="坯布下达",
        operator_id=user_id,
        remark=f"坯布负责人: {yarn_user.display_name}. {remark}".strip(),
    )
    db.add(log)
    db.commit()
    db.refresh(item)

    # Non-blocking WeCom notification
    try:
        notify_yarn_plan_released(
            db, item.contract.contract_no,
            item.spec_description or "",
            yarn_user.wecom_userid if yarn_user else None,
        )
    except Exception as e:
        logger.warning(f"通知发送失败（不影响业务）: {e}")

    return item, log


def get_item_logs(db: Session, item_id: int):
    """Get production logs for a contract item."""
    return db.query(ProductionLog).filter(
        ProductionLog.contract_item_id == item_id
    ).order_by(ProductionLog.created_at.desc()).all()


def get_contract_logs(db: Session, contract_id: int):
    """Get all production logs for a contract."""
    return db.query(ProductionLog).filter(
        ProductionLog.contract_id == contract_id
    ).order_by(ProductionLog.created_at.desc()).options(
        joinedload(ProductionLog.operator)
    ).all()


def get_my_tasks(db: Session, user_id: int):
    """Get contract items assigned to this user as yarn_plan_user (外协人员)."""
    return db.query(ContractItem).filter(
        ContractItem.yarn_plan_user_id == user_id,
        ContractItem.cancel_reason.is_(None),
    ).options(
        joinedload(ContractItem.contract),
        joinedload(ContractItem.spec),
    ).order_by(ContractItem.id.desc()).all()


def push_down_item_to_process_sheet(db: Session, item_id: int, user_id: int, process_remark: str = ""):
    """行项目下推为工艺单（一个行项目生成一张独立的工艺单）。"""
    item = db.query(ContractItem).options(
        joinedload(ContractItem.spec)
    ).filter(ContractItem.id == item_id).first()
    if not item:
        raise HTTPException(status_code=404, detail="行项目不存在")

    contract = db.query(Contract).options(
        joinedload(Contract.customer)
    ).filter(Contract.id == item.contract_id).first()
    if not contract or contract.is_deleted:
        raise HTTPException(status_code=404, detail="合同不存在")
    if contract.status == "草稿":
        raise HTTPException(status_code=400, detail="合同未确认，无法下推")

    # Check if this item already has a non-deleted process sheet
    existing = db.query(ProcessSheetItem).join(ProcessSheet).filter(
        ProcessSheetItem.contract_item_id == item_id,
        ProcessSheet.is_deleted == False,
    ).first()
    if existing:
        raise HTTPException(status_code=400, detail="该行项目已下推工艺单")

    # Each item gets its own process sheet
    from datetime import date
    today = date.today()
    prefix = today.strftime('%Y%m')
    count = db.query(ProcessSheet).filter(
        ProcessSheet.sheet_no.like(f"{prefix}-%")
    ).count()
    sheet = ProcessSheet(
        contract_id=contract.id,
        sheet_no=f"{prefix}-{count + 1:03d}",
        confirm_version_no=0,  # 工艺单独立版本体系，初始 V0
        status="草稿",
        created_by=contract.updated_by or contract.created_by,
        updated_by=contract.updated_by or contract.created_by,
        contract_snapshot={
            "contract_no": contract.contract_no,
            "customer_name": contract.customer.name if contract.customer else None,
            "contract_date": str(contract.contract_date) if contract.contract_date else None,
            "delivery_date": str(item.delivery_date) if item.delivery_date else None,
            "spec_description": item.spec_description,
            "spec_name": item.spec.spec_name if item.spec else None,
            "qty": float(item.qty) if item.qty else 0,
            "packaging_type": item.packaging_type or "",
            "is_pressed": item.is_pressed or False,
            "pattern_count": item.pattern_count or 0,
            "remark": item.remark or "",
            "latest_confirm_version": contract.latest_confirm_version or 0,
        },
    )
    db.add(sheet)
    db.flush()

    # Create process sheet item (one item per sheet)
    sheet_item = ProcessSheetItem(
        process_sheet_id=sheet.id,
        contract_item_id=item.id,
        line_no=1,
        spec_id=item.spec_id,
        is_pressed=item.is_pressed,
        packaging_type=item.packaging_type or "",
        delivery_date=item.delivery_date,
        pattern_count=item.pattern_count or 0,
        pattern_data=item.pattern_data,
        pattern_code=item.pattern_code or "",
        color_a=item.color_a or "",
        image_a_1=item.image_a_1 or "",
        image_a_2=item.image_a_2 or "",
        image_a_3=item.image_a_3 or "",
        color_b=item.color_b or "",
        image_b_1=item.image_b_1 or "",
        image_b_2=item.image_b_2 or "",
        image_b_3=item.image_b_3 or "",
        remark=item.remark or "",
        process_remark=process_remark,
        qty=item.qty or 0,
    )
    db.add(sheet_item)

    # Update contract status to 已下发 (if it was confirmed)
    if contract.status == "确认":
        contract.status = "已下发"

    user = db.query(User).filter(User.id == user_id).first()
    log = ProductionLog(
        contract_id=contract.id,
        contract_item_id=item.id,
        from_status=item.production_status,
        to_status="push_down",
        operation_type="推进",
        operator_id=user_id,
        remark=f"下推工艺单: {sheet.sheet_no}",
    )
    db.add(log)
    db.commit()
    db.refresh(sheet)
    return sheet


def get_process_sheet_for_item(db: Session, item_id: int) -> dict | None:
    """Get process sheet info for a contract item."""
    sheet_item = db.query(ProcessSheetItem).filter(
        ProcessSheetItem.contract_item_id == item_id
    ).options(
        joinedload(ProcessSheetItem.process_sheet),
    ).first()
    if not sheet_item or not sheet_item.process_sheet or sheet_item.process_sheet.is_deleted:
        return None
    sheet = sheet_item.process_sheet
    return {
        "id": sheet.id,
        "sheet_no": sheet.sheet_no,
        "status": sheet.status,
        "confirm_version_no": sheet.confirm_version_no,
    }


def item_has_process_sheet(db: Session, item_id: int) -> bool:
    """Check if a contract item has already been pushed down to a process sheet."""
    existing = db.query(ProcessSheetItem).filter(
        ProcessSheetItem.contract_item_id == item_id
    ).first()
    return existing is not None
