from sqlalchemy.orm import Session
from app.models.basic_data import BasicData
from app.schemas.basic_data import BasicDataCreate, BasicDataUpdate


def list_by_category(db: Session, category: str):
    return db.query(BasicData).filter(
        BasicData.category == category
    ).order_by(BasicData.sort_order, BasicData.id).all()


def create_item(db: Session, data: BasicDataCreate):
    item = BasicData(**data.model_dump())
    db.add(item)
    db.commit()
    db.refresh(item)
    return item


def update_item(db: Session, id: int, data: BasicDataUpdate):
    item = db.query(BasicData).filter(BasicData.id == id).first()
    if not item:
        return None
    for field, value in data.model_dump(exclude_unset=True).items():
        setattr(item, field, value)
    db.commit()
    db.refresh(item)
    return item


def delete_item(db: Session, id: int):
    item = db.query(BasicData).filter(BasicData.id == id).first()
    if not item:
        return False
    db.delete(item)
    db.commit()
    return True


def get_color_mapping(db: Session):
    """Return dict of color → binding_color_no"""
    items = list_by_category(db, "color")
    return {item.code: item.value for item in items if item.value}
