from sqlalchemy.orm import Session
from app.models.spec import Spec
from app.models.contract import Contract
from app.schemas.spec import SpecCreate, SpecUpdate
from fastapi import HTTPException


def generate_spec_name(spec) -> str:
    return f"{spec.length}*{spec.width}/{spec.weight}/{spec.layer_type}"


def _validate_weight(weight: str):
    if "KG" not in weight.upper():
        raise HTTPException(status_code=400, detail="毛毯重量必须包含 KG 单位，如 4KG")


def list_specs(db: Session, keyword: str = ""):
    q = db.query(Spec).filter(Spec.is_deleted == False)
    if keyword:
        q = q.filter(Spec.spec_name.like(f"%{keyword}%"))
    specs = q.order_by(Spec.id.desc()).all()

    # Check which specs are referenced by active contracts
    spec_ids = [s.id for s in specs]
    if spec_ids:
        used_ids = {
            row[0] for row in db.query(Contract.spec_id).filter(
                Contract.spec_id.in_(spec_ids),
                Contract.is_deleted == False,
            ).distinct().all()
        }
    else:
        used_ids = set()

    for s in specs:
        s.is_in_use = s.id in used_ids
    return specs


def get_spec(db: Session, id: int):
    spec = db.query(Spec).filter(Spec.id == id, Spec.is_deleted == False).first()
    if spec:
        spec.is_in_use = db.query(Contract).filter(
            Contract.spec_id == id,
            Contract.is_deleted == False,
        ).first() is not None
    return spec


def find_spec_by_name(db: Session, name: str):
    return db.query(Spec).filter(Spec.spec_name == name, Spec.is_deleted == False).first()


def create_spec(db: Session, data: SpecCreate, username: str):
    _validate_weight(data.weight)
    spec_name = f"{data.length}*{data.width}/{data.weight}/{data.layer_type}"
    if find_spec_by_name(db, spec_name):
        raise HTTPException(status_code=400, detail=f"规格 '{spec_name}' 已存在")
    spec = Spec(
        length=data.length, width=data.width,
        weight=data.weight, layer_type=data.layer_type,
        created_by=username, updated_by=username,
    )
    spec.spec_name = spec_name
    spec.spec_description = spec_name
    db.add(spec)
    db.commit()
    db.refresh(spec)
    return spec


def update_spec(db: Session, id: int, data: SpecUpdate, username: str):
    spec = get_spec(db, id)
    if not spec:
        return None
    if getattr(spec, 'is_in_use', False) or db.query(Contract).filter(
        Contract.spec_id == id, Contract.is_deleted == False,
    ).first():
        raise HTTPException(status_code=400, detail="该规格已被合同引用，不可修改")
    for field, value in data.model_dump(exclude_unset=True).items():
        setattr(spec, field, value)
    spec.spec_name = generate_spec_name(spec)
    spec.spec_description = spec.spec_name
    # Check duplicate after field changes
    existing = find_spec_by_name(db, spec.spec_name)
    if existing and existing.id != id:
        raise HTTPException(status_code=400, detail=f"规格 '{spec.spec_name}' 已存在")
    spec.updated_by = username
    db.commit()
    db.refresh(spec)
    return spec


def delete_spec(db: Session, id: int):
    spec = db.query(Spec).filter(Spec.id == id, Spec.is_deleted == False).first()
    if not spec:
        return False
    spec.is_deleted = True
    db.commit()
    return True


def clone_spec(db: Session, id: int, username: str):
    spec = db.query(Spec).filter(Spec.id == id, Spec.is_deleted == False).first()
    if not spec:
        raise HTTPException(status_code=404, detail="规格不存在")
    new_spec = Spec(
        length=spec.length, width=spec.width,
        weight=spec.weight, layer_type=spec.layer_type,
        created_by=username, updated_by=username,
    )
    new_spec.spec_name = generate_spec_name(new_spec)
    new_spec.spec_description = new_spec.spec_name
    db.add(new_spec)
    db.commit()
    db.refresh(new_spec)
    return new_spec
