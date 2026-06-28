from sqlalchemy.orm import Session, joinedload
from sqlalchemy import update
from app.models.process_step import ProcessStep
from app.models.process_step_assignee import ProcessStepAssignee
from app.schemas.process_step import ProcessStepCreate, ProcessStepUpdate
from fastapi import HTTPException


def list_steps(db: Session, include_inactive: bool = False):
    q = db.query(ProcessStep).options(joinedload(ProcessStep.assignees))
    if not include_inactive:
        q = q.filter(ProcessStep.is_active == True)
    return q.order_by(ProcessStep.sort_order, ProcessStep.id).all()


def get_step(db: Session, id: int):
    return db.query(ProcessStep).options(
        joinedload(ProcessStep.assignees)
    ).filter(ProcessStep.id == id).first()


def create_step(db: Session, data: ProcessStepCreate):
    existing = db.query(ProcessStep).filter(
        ProcessStep.step_code == data.step_code
    ).first()
    if existing:
        raise HTTPException(status_code=400, detail=f"工序编码 {data.step_code} 已存在")
    step = ProcessStep(**data.model_dump())
    db.add(step)
    db.commit()
    db.refresh(step)
    return step


def update_step(db: Session, id: int, data: ProcessStepUpdate):
    step = get_step(db, id)
    if not step:
        raise HTTPException(status_code=404, detail="工序不存在")
    for field, value in data.model_dump(exclude_unset=True).items():
        setattr(step, field, value)
    db.commit()
    db.refresh(step)
    return step


def delete_step(db: Session, id: int):
    step = db.query(ProcessStep).filter(ProcessStep.id == id).first()
    if not step:
        raise HTTPException(status_code=404, detail="工序不存在")
    # Check if any contract_items reference this step's code
    from app.models.contract_item import ContractItem
    in_use = db.query(ContractItem).filter(
        ContractItem.production_status == step.step_code
    ).first()
    if in_use:
        raise HTTPException(status_code=400, detail="该工序已被使用，无法删除")
    db.delete(step)
    db.commit()
    return {"ok": True}


def set_assignees(db: Session, step_id: int, user_ids: list[int]):
    step = get_step(db, step_id)
    if not step:
        raise HTTPException(status_code=404, detail="工序不存在")
    # Remove existing assignees
    db.query(ProcessStepAssignee).filter(
        ProcessStepAssignee.process_step_id == step_id
    ).delete()
    # Add new assignees
    for uid in user_ids:
        db.add(ProcessStepAssignee(process_step_id=step_id, user_id=uid))
    db.commit()
    return get_step(db, step_id)


def get_ordered_step_codes(db: Session) -> list[str]:
    """Return ordered list of step codes for state machine validation."""
    steps = db.query(ProcessStep).filter(
        ProcessStep.is_active == True
    ).order_by(ProcessStep.sort_order, ProcessStep.id).all()
    return [s.step_code for s in steps]
