from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
import json
from app.database import get_db
from app.dependencies import get_current_user, require_permission
from app.models.user import User
from app.models.system_config import SystemConfig
from app.services.permission import (
    get_all_permissions, get_all_permission_definitions,
    reload_cache
)

router = APIRouter(prefix="/api/permissions", tags=["permissions"])


@router.get("/definitions")
def get_definitions():
    """Return the canonical permission list grouped by module."""
    return get_all_permission_definitions()


@router.get("")
def get_permissions(
    db: Session = Depends(get_db),
    current_user: User = Depends(require_permission("settings:permissions:manage")),
):
    """Return the current role->permissions mapping."""
    return get_all_permissions(db)


@router.put("")
def update_permissions(
    data: dict,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_permission("settings:permissions:manage")),
):
    """Update the role->permissions mapping."""
    config = db.query(SystemConfig).filter(
        SystemConfig.config_key == "role_permissions"
    ).first()
    if not config:
        config = SystemConfig(config_key="role_permissions", config_value="{}")
        db.add(config)
    config.config_value = json.dumps({"roles": data}, ensure_ascii=False)
    db.commit()
    reload_cache(db)
    return {"message": "权限配置已更新"}


@router.get("/my")
def get_my_permissions(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Return all permissions for the current user's role."""
    all_perms = get_all_permissions(db)
    return all_perms.get(current_user.role, [])
