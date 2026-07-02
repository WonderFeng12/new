from sqlalchemy.orm import Session
from app.models.spec import Spec
from app.models.contract import Contract
from app.models.contract_item import ContractItem
from app.schemas.spec import SpecCreate, SpecUpdate
from fastapi import HTTPException


def generate_spec_name(spec) -> str:
    return f"{spec.length}*{spec.width}/{spec.weight}/{spec.layer_type}"


def _validate_numeric(value: str, field_name: str):
    import re
    if not re.match(r'^\d+(\.\d+)?$', value):
        raise HTTPException(status_code=400, detail=f"{field_name}必须是数字")
    return value


def _validate_and_normalize_weight(weight: str) -> str:
    weight = weight.strip().upper().replace("KG", "").strip()
    _validate_numeric(weight, "毛毯总量")
    return weight + "KG"


def list_specs(db: Session, keyword: str = ""):
    q = db.query(Spec).filter(Spec.is_deleted == False)
    if keyword:
        q = q.filter(Spec.spec_name.like(f"%{keyword}%"))
    specs = q.order_by(Spec.id.desc()).all()

    # Check which specs are referenced by active contracts
    spec_ids = [s.id for s in specs]
    used_ids = set()
    if spec_ids:
        # Check direct contract references (legacy)
        contract_used = {
            row[0] for row in db.query(Contract.spec_id).filter(
                Contract.spec_id.in_(spec_ids),
                Contract.is_deleted == False,
            ).distinct().all()
        }
        # Check contract item references
        item_used = {
            row[0] for row in db.query(ContractItem.spec_id).filter(
                ContractItem.spec_id.in_(spec_ids),
            ).distinct().all()
        }
        used_ids = contract_used | item_used

    for s in specs:
        s.is_in_use = s.id in used_ids
    return specs


def get_spec(db: Session, id: int):
    spec = db.query(Spec).filter(Spec.id == id, Spec.is_deleted == False).first()
    if spec:
        in_contract = db.query(Contract).filter(
            Contract.spec_id == id,
            Contract.is_deleted == False,
        ).first() is not None
        in_item = db.query(ContractItem).filter(
            ContractItem.spec_id == id,
        ).first() is not None
        spec.is_in_use = in_contract or in_item
    return spec


def find_spec_by_name(db: Session, name: str):
    return db.query(Spec).filter(Spec.spec_name == name, Spec.is_deleted == False).first()


def create_spec(db: Session, data: SpecCreate, username: str):
    _validate_numeric(data.length, "毛毯尺寸长")
    _validate_numeric(data.width, "毛毯尺寸宽")
    weight = _validate_and_normalize_weight(data.weight)
    spec_name = f"{data.length}*{data.width}/{weight}/{data.layer_type}"
    if find_spec_by_name(db, spec_name):
        raise HTTPException(status_code=400, detail=f"规格 '{spec_name}' 已存在")
    spec = Spec(
        length=data.length, width=data.width,
        weight=weight, layer_type=data.layer_type,
        created_by=username, updated_by=username,
    )
    spec.spec_name = spec_name
    spec.spec_description = spec_name
    db.add(spec)
    db.commit()
    db.refresh(spec)
    return spec


def update_spec(db: Session, id: int, data: SpecUpdate, username: str, cascade: bool = False):
    spec = get_spec(db, id)
    if not spec:
        return None
    in_use = getattr(spec, 'is_in_use', False) or db.query(Contract).filter(
        Contract.spec_id == id, Contract.is_deleted == False,
    ).first() or db.query(ContractItem).filter(
        ContractItem.spec_id == id,
    ).first()
    if in_use and not cascade:
        raise HTTPException(status_code=400, detail="该规格已被合同引用，不可修改")
    update_data = data.model_dump(exclude_unset=True)
    if "length" in update_data:
        _validate_numeric(update_data["length"], "毛毯尺寸长")
    if "width" in update_data:
        _validate_numeric(update_data["width"], "毛毯尺寸宽")
    if "weight" in update_data:
        update_data["weight"] = _validate_and_normalize_weight(update_data["weight"])
    for field, value in update_data.items():
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
    in_contract = db.query(Contract).filter(
        Contract.spec_id == id, Contract.is_deleted == False,
    ).first() is not None
    in_item = db.query(ContractItem).filter(
        ContractItem.spec_id == id,
    ).first() is not None
    if in_contract or in_item:
        raise HTTPException(status_code=400, detail="该规格已被合同引用，不可删除")
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
