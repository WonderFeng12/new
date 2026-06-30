from fastapi import Depends, HTTPException
from sqlalchemy.orm import Session
from app.services.auth import get_current_user
from app.models.user import User
from app.database import get_db
from app.services.permission import check_permission


def require_role(*roles: str):
    def checker(current_user: User = Depends(get_current_user)):
        if current_user.role not in roles:
            raise HTTPException(status_code=403, detail="权限不足")
        return current_user
    return checker


def require_permission(permission: str):
    """FastAPI dependency: check the current user's role has the given permission."""
    def checker(
        current_user: User = Depends(get_current_user),
        db: Session = Depends(get_db),
    ):
        if not check_permission(db, current_user.role, permission):
            raise HTTPException(
                status_code=403,
                detail=f"权限不足: 需要 {permission}"
            )
        return current_user
    return checker
