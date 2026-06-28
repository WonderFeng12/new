import json
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
    item.cancel_quantities = quantities
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


def push_down_item_to_process_sheet(db: Session, item_id: int, user_id: int):
    """行项目下推为工艺单。"""
    item = db.query(ContractItem).filter(ContractItem.id == item_id).first()
    if not item:
        raise HTTPException(status_code=404, detail="行项目不存在")

    contract = db.query(Contract).filter(Contract.id == item.contract_id).first()
    if not contract or contract.is_deleted:
        raise HTTPException(status_code=404, detail="合同不存在")
    if contract.status == "草稿":
        raise HTTPException(status_code=400, detail="合同未确认，无法下推")

    # Check if this item already has a process sheet item
    existing = db.query(ProcessSheetItem).filter(
        ProcessSheetItem.contract_item_id == item_id
    ).first()
    if existing:
        raise HTTPException(status_code=400, detail="该行项目已下推工艺单")

    # Find existing process sheet for this contract, or create one
    sheet = db.query(ProcessSheet).filter(
        ProcessSheet.contract_id == contract.id,
        ProcessSheet.is_deleted == False,
    ).first()
    if not sheet:
        from datetime import date
        today = date.today()
        seq = db.query(ProcessSheet).count() + 1
        sheet = ProcessSheet(
            contract_id=contract.id,
            sheet_no=f"GY{today.strftime('%Y%m')}{seq:04d}",
            confirm_version_no=0,
            status="草稿",
            created_by=contract.updated_by or contract.created_by,
            updated_by=contract.updated_by or contract.created_by,
        )
        db.add(sheet)
        db.flush()

    # Create process sheet item
    sheet_item = ProcessSheetItem(
        process_sheet_id=sheet.id,
        contract_item_id=item.id,
        line_no=item.line_no,
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


def item_has_process_sheet(db: Session, item_id: int) -> bool:
    """Check if a contract item has already been pushed down to a process sheet."""
    existing = db.query(ProcessSheetItem).filter(
        ProcessSheetItem.contract_item_id == item_id
    ).first()
    return existing is not None
