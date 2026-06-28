from fastapi import APIRouter, Depends
from pydantic import BaseModel
from typing import Optional
from sqlalchemy.orm import Session
from app.database import get_db
from app.dependencies import get_current_user, require_role
from app.models.user import User
from app.schemas.process_step import (
    ProcessStepCreate, ProcessStepUpdate, ProcessStepWithAssignees, AssigneesUpdate
)
from app.schemas.production_log import ProductionLogOut
from app.schemas.system_config import SystemConfigUpdate, SystemConfigOut
from app.services import process_step as step_service
from app.services import production as prod_service

router = APIRouter(prefix="/api", tags=["production"])


# ── Process Step CRUD ──


@router.get("/process-steps")
def list_steps(
    include_inactive: bool = False,
    db: Session = Depends(get_db),
):
    steps = step_service.list_steps(db, include_inactive)
    result = []
    for s in steps:
        step_data = {
            "id": s.id,
            "step_code": s.step_code,
            "step_name": s.step_name,
            "sort_order": s.sort_order,
            "is_active": s.is_active,
            "created_at": s.created_at,
            "assignees": [
                {
                    "id": a.user.id,
                    "display_name": a.user.display_name,
                    "role": a.user.role,
                    "wecom_userid": a.user.wecom_userid,
                }
                for a in s.assignees if a.user
            ],
        }
        result.append(step_data)
    return result


@router.post("/process-steps")
def create_step(
    data: ProcessStepCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_role("销售经理", "生产专员")),
):
    return step_service.create_step(db, data)


@router.put("/process-steps/{id}")
def update_step(
    id: int,
    data: ProcessStepUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_role("销售经理", "生产专员")),
):
    return step_service.update_step(db, id, data)


@router.delete("/process-steps/{id}")
def delete_step(
    id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_role("销售经理", "生产专员")),
):
    return step_service.delete_step(db, id)


@router.put("/process-steps/{id}/assignees")
def set_assignees(
    id: int,
    data: AssigneesUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_role("销售经理", "生产专员")),
):
    return step_service.set_assignees(db, id, data.user_ids)


# ── Contract Item Operations ──


class AdvanceRequest(BaseModel):
    remark: Optional[str] = ""


class RollbackRequest(BaseModel):
    remark: Optional[str] = ""


class ReworkRequest(BaseModel):
    target_step: str
    remark: Optional[str] = ""


class CancelRequest(BaseModel):
    reason: str
    quantities: Optional[dict[str, float]] = None


class YarnPlanRequest(BaseModel):
    yarn_plan_user_id: int
    remark: Optional[str] = ""


@router.post("/contract-items/{id}/advance")
def advance_item(
    id: int,
    req: AdvanceRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    item, log = prod_service.advance_item(db, id, current_user.id, req.remark)
    return {"message": "推进成功", "production_status": item.production_status}


@router.post("/contract-items/{id}/rollback")
def rollback_item(
    id: int,
    req: RollbackRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    item, log = prod_service.rollback_item(db, id, current_user.id, req.remark)
    return {"message": "回退成功", "production_status": item.production_status}


@router.post("/contract-items/{id}/rework")
def rework_item(
    id: int,
    req: ReworkRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    item, log = prod_service.rework_item(db, id, req.target_step, current_user.id, req.remark)
    return {"message": "返工成功", "production_status": item.production_status}


@router.post("/contract-items/{id}/cancel")
def cancel_item(
    id: int,
    req: CancelRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    item, log = prod_service.cancel_item(db, id, current_user.id, req.reason, req.quantities)
    return {"message": "已取消", "production_status": item.production_status}


@router.post("/contract-items/{id}/yarn-plan")
def release_yarn_plan(
    id: int,
    req: YarnPlanRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_role("销售经理", "生产专员")),
):
    item, log = prod_service.release_yarn_plan(db, id, current_user.id, req.yarn_plan_user_id, req.remark)
    return {"message": "坯布计划已下达", "production_status": item.production_status}


@router.get("/contract-items/{id}/logs")
def get_item_logs(
    id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    logs = prod_service.get_item_logs(db, id)
    result = []
    for log in logs:
        log_data = {
            "id": log.id,
            "contract_id": log.contract_id,
            "contract_item_id": log.contract_item_id,
            "from_status": log.from_status,
            "to_status": log.to_status,
            "operation_type": log.operation_type,
            "operator_id": log.operator_id,
            "operator_name": log.operator.display_name if log.operator else "",
            "remark": log.remark,
            "created_at": log.created_at,
        }
        result.append(log_data)
    return result


@router.get("/contracts/{id}/production-logs")
def get_contract_logs(
    id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    logs = prod_service.get_contract_logs(db, id)
    result = []
    for log in logs:
        log_data = {
            "id": log.id,
            "contract_id": log.contract_id,
            "contract_item_id": log.contract_item_id,
            "from_status": log.from_status,
            "to_status": log.to_status,
            "operation_type": log.operation_type,
            "operator_id": log.operator_id,
            "operator_name": log.operator.display_name if log.operator else "",
            "remark": log.remark,
            "created_at": log.created_at,
        }
        result.append(log_data)
    return result


# ── My Tasks (for 外协人员) ──


@router.get("/my-tasks")
def get_my_tasks(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    items = prod_service.get_my_tasks(db, current_user.id)
    result = []
    for item in items:
        result.append({
            "id": item.id,
            "contract_id": item.contract_id,
            "contract_no": item.contract.contract_no if item.contract else "",
            "line_no": item.line_no,
            "spec_description": item.spec_description or f"规格#{item.spec_id}",
            "production_status": item.production_status,
            "qty": float(item.qty) if item.qty else 0,
        })
    return result


# ── System Config (WeCom settings) ──


@router.get("/settings/wecom")
def get_wecom_settings(
    db: Session = Depends(get_db),
    current_user: User = Depends(require_role("销售经理", "生产专员")),
):
    from app.models.system_config import SystemConfig
    configs = db.query(SystemConfig).filter(
        SystemConfig.config_key.in_(["wecom_webhook_url", "production_notify_enabled"])
    ).all()
    result = {c.config_key: c.config_value for c in configs}
    return result


@router.put("/settings/wecom")
def update_wecom_settings(
    data: dict[str, str],
    db: Session = Depends(get_db),
    current_user: User = Depends(require_role("销售经理", "生产专员")),
):
    from app.models.system_config import SystemConfig
    for key, value in data.items():
        if key not in ("wecom_webhook_url", "production_notify_enabled"):
            continue
        config = db.query(SystemConfig).filter(
            SystemConfig.config_key == key
        ).first()
        if config:
            config.config_value = value
        else:
            db.add(SystemConfig(config_key=key, config_value=value))
    db.commit()
    return {"ok": True}


@router.put("/users/me/wecom")
def update_my_wecom(
    data: dict[str, str],
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    current_user.wecom_userid = data.get("wecom_userid", "")
    db.commit()
    return {"ok": True}


# ── User list (for assignee selection) ──


@router.get("/users")
def list_users(db: Session = Depends(get_db)):
    users = db.query(User).filter(User.is_deleted == False).all()
    return [
        {
            "id": u.id,
            "display_name": u.display_name,
            "role": u.role,
            "wecom_userid": u.wecom_userid,
            "username": u.username,
        }
        for u in users
    ]
