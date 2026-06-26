from sqlalchemy.orm import Session
from app.models.spec import Spec
from app.schemas.spec import SpecCreate, SpecUpdate


def generate_spec_name(spec) -> str:
    return f"{spec.length}*{spec.width}/{spec.weight}/{spec.layer_type}"


def list_specs(db: Session, keyword: str = ""):
    q = db.query(Spec).filter(Spec.is_deleted == False)
    if keyword:
        q = q.filter(Spec.spec_name.like(f"%{keyword}%"))
    return q.order_by(Spec.id.desc()).all()


def get_spec(db: Session, id: int):
    return db.query(Spec).filter(Spec.id == id, Spec.is_deleted == False).first()


def find_spec_by_name(db: Session, name: str):
    return db.query(Spec).filter(Spec.spec_name == name, Spec.is_deleted == False).first()


def create_spec(db: Session, data: SpecCreate, username: str):
    spec = Spec(
        length=data.length, width=data.width,
        weight=data.weight, layer_type=data.layer_type,
        created_by=username, updated_by=username,
    )
    spec.spec_name = generate_spec_name(spec)
    spec.spec_description = spec.spec_name
    db.add(spec)
    db.commit()
    db.refresh(spec)
    return spec


def update_spec(db: Session, id: int, data: SpecUpdate, username: str):
    spec = get_spec(db, id)
    if not spec:
        return None
    for field, value in data.model_dump(exclude_unset=True).items():
        setattr(spec, field, value)
    spec.spec_name = generate_spec_name(spec)
    spec.spec_description = spec.spec_name
    spec.updated_by = username
    db.commit()
    db.refresh(spec)
    return spec


def delete_spec(db: Session, id: int):
    spec = get_spec(db, id)
    if not spec:
        return False
    spec.is_deleted = True
    db.commit()
    return True
