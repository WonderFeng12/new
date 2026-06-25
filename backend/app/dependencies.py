from fastapi import Depends, HTTPException
from app.services.auth import get_current_user
from app.models.user import User


def require_role(*roles: str):
    def checker(current_user: User = Depends(get_current_user)):
        if current_user.role not in roles:
            raise HTTPException(status_code=403, detail="权限不足")
        return current_user
    return checker
