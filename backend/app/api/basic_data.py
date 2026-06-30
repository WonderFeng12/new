from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from app.database import get_db
from app.dependencies import get_current_user, require_permission
from app.models.user import User
from app.schemas.basic_data import BasicDataCreate, BasicDataUpdate, BasicDataOut
from app.services import basic_data as service

router = APIRouter(prefix="/api/basic-data", tags=["basic-data"])


@router.get("/{category}")
def list_category(category: str, db: Session = Depends(get_db)):
    items = service.list_by_category(db, category)
    return items


@router.post("/{category}")
def create_item(
    category: str,
    data: BasicDataCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_permission("basic_data:manage")),
):
    data.category = category
    return service.create_item(db, data)


@router.put("/{category}/{id}")
def update_item(
    category: str,
    id: int,
    data: BasicDataUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_permission("basic_data:manage")),
):
    item = service.update_item(db, id, data)
    if not item:
        from fastapi import HTTPException
        raise HTTPException(status_code=404, detail="Item not found")
    return item


@router.delete("/{category}/{id}")
def delete_item(
    category: str,
    id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_permission("basic_data:manage")),
):
    ok = service.delete_item(db, id)
    if not ok:
        from fastapi import HTTPException
        raise HTTPException(status_code=404, detail="Item not found")
    return {"ok": True}


@router.get("/mapping/color")
def get_color_mapping(
    db: Session = Depends(get_db),
):
    return service.get_color_mapping(db)
