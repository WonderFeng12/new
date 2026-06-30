from fastapi import APIRouter, Depends, HTTPException, Request
from sqlalchemy.orm import Session
from pydantic import BaseModel
from app.database import get_db
from app.schemas.contract import ContractCreate, ContractUpdate, ContractOut
from app.services import contract as service
from app.services import confirm_image as confirm_image_service
from app.services.notify import notify_contract_ready_for_confirm
from app.dependencies import get_current_user, require_permission
from app.models.user import User


class ManualConfirmRequest(BaseModel):
    remark: str

router = APIRouter(prefix="/api/contracts", tags=["contracts"])


@router.get("", response_model=list[ContractOut])
def list_all(
    keyword: str = "",
    db: Session = Depends(get_db),
    current_user: User = Depends(require_permission("contract:view")),
):
    return service.list_contracts(db, keyword, current_user.id, current_user.role)


@router.get("/next-no")
def next_contract_no(
    customer_id: int = None,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_permission("contract:create")),
):
    return {"contract_no": service.generate_contract_no(db, customer_id)}


@router.get("/available", response_model=list[ContractOut])
def list_available(
    db: Session = Depends(get_db),
    current_user: User = Depends(require_permission("contract:view")),
):

    return service.get_available_contracts(db)


@router.get("/{id}", response_model=ContractOut)
def get_one(
    id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_permission("contract:view")),
):

    c = service.get_contract(db, id)
    if not c:
        raise HTTPException(status_code=404, detail="合同不存在")
    return c


@router.post("", response_model=ContractOut)
def create(
    data: ContractCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_permission("contract:create")),
):

    return service.create_contract(db, data, current_user.display_name or current_user.username)


@router.put("/{id}", response_model=ContractOut)
def update(
    id: int,
    data: ContractUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_permission("contract:edit")),
):

    result = service.update_contract(db, id, data, current_user.display_name or current_user.username, current_user.role)
    if not result:
        raise HTTPException(status_code=404, detail="合同不存在")
    return result


@router.delete("/{id}")
def delete(
    id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_permission("contract:delete")),
):

    if not service.delete_contract(db, id):
        raise HTTPException(status_code=404, detail="合同不存在")
    return {"message": "已删除"}


@router.post("/{id}/manual-confirm", response_model=ContractOut)
def manual_confirm(
    id: int,
    data: ManualConfirmRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_permission("contract:manual_confirm")),
):

    if not data.remark or not data.remark.strip():
        raise HTTPException(status_code=400, detail="确认意见不能为空")
    result = service.manual_confirm_contract(db, id, current_user.id, data.remark.strip())
    if not result:
        raise HTTPException(status_code=404, detail="合同不存在")
    return result


@router.post("/{id}/request-confirm")
def request_confirm(
    id: int,
    request: Request,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_permission("contract:request_confirm")),
):
    """业务员完成合同后，发送企微通知请求销售经理确认。"""
    c = service.get_contract(db, id)
    if not c:
        raise HTTPException(status_code=404, detail="合同不存在")
    if c.status != "草稿":
        raise HTTPException(status_code=400, detail="仅草稿合同可请求确认")
    from datetime import datetime as dt
    service.update_confirm_request_time(db, id, dt.now())
    # Use configured system URL, fall back to request base
    from app.models.system_config import SystemConfig
    sys_url_config = db.query(SystemConfig).filter(
        SystemConfig.config_key == "system_base_url"
    ).first()
    base_url = sys_url_config.config_value if sys_url_config else str(request.base_url).rstrip("/")
    notify_contract_ready_for_confirm(
        db, c.contract_no,
        current_user.display_name or current_user.username,
        base_url=base_url,
        contract_id=id,
    )
    return {"message": "已发送确认请求，明天8点将自动催办"}


@router.post("/{id}/reopen-edit")
def reopen_edit(
    id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_permission("contract:reopen_edit")),
):
    """重新打开已确认/已下发的合同进行编辑（记录日志）。"""

    service.reopen_edit(db, id, current_user.id)
    return {"message": "已记录重新编辑操作"}


@router.get("/{id}/versions")
def get_versions(
    id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_permission("contract:view_versions")),
):
    """返回确认图版本历史。"""

    versions = confirm_image_service.get_versions(db, id)
    return [
        {
            "id": v.id,
            "version_no": v.version_no,
            "generated_at": v.generated_at.isoformat() if v.generated_at else None,
            "generated_by": v.generated_by,
            "change_log": v.change_log,
            "is_confirmed": v.is_confirmed,
            "confirmed_at": v.confirmed_at.isoformat() if v.confirmed_at else None,
            "confirmed_by": v.confirmed_by,
            "image_path": v.image_path,
        }
        for v in versions
    ]


@router.post("/{id}/confirm-image")
def generate_confirm_image(
    id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_permission("contract:generate_confirm_image")),
):
    """生成确认图。"""

    username = current_user.display_name or current_user.username
    image = confirm_image_service.generate_confirm_image(db, id, username, image_path="")
    return {
        "id": image.id,
        "version_no": image.version_no,
        "generated_at": image.generated_at.isoformat() if image.generated_at else None,
        "generated_by": image.generated_by,
        "change_log": image.change_log,
        "is_confirmed": image.is_confirmed,
        "image_path": image.image_path,
    }
