from sqlalchemy.orm import Session
from app.models.spec import Spec
from app.schemas.spec import SpecCreate, SpecUpdate

def build_description(spec: Spec) -> str:
    parts = [spec.spec_name, spec.weight, f"({spec.layer_type})"]
    if spec.splice_method:
        parts.append(spec.splice_method)
    return "+".join(parts)

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
        spec_name=data.spec_name, weight=data.weight,
        layer_type=data.layer_type, splice_method=data.splice_method or "",
        created_by=username, updated_by=username,
    )
    spec.spec_description = build_description(spec)
    db.add(spec); db.commit(); db.refresh(spec)
    return spec

def update_spec(db: Session, id: int, data: SpecUpdate, username: str):
    spec = get_spec(db, id)
    if not spec: return None
    for field, value in data.model_dump(exclude_unset=True).items():
        setattr(spec, field, value)
    spec.spec_description = build_description(spec)
    spec.updated_by = username
    db.commit(); db.refresh(spec)
    return spec

def delete_spec(db: Session, id: int):
    spec = get_spec(db, id)
    if not spec: return False
    spec.is_deleted = True
    db.commit()
    return True
