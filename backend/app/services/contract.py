from sqlalchemy.orm import Session, joinedload
from app.models.contract import Contract
from app.models.contract_item import ContractItem
from sqlalchemy.orm import defaultload
from app.schemas.contract import ContractCreate, ContractUpdate
from app.schemas.contract_item import ContractItemCreate
from fastapi import HTTPException


def generate_contract_no(db: Session) -> str:
    last = db.query(Contract).order_by(Contract.id.desc()).first()
    seq = (last.id + 1) if last else 1
    from datetime import date
    today = date.today()
    return f"HT{today.strftime('%Y%m')}{seq:04d}"


def list_contracts(
    db: Session,
    keyword: str = "",
    user_id: int | None = None,
    role: str = "",
):
    q = db.query(Contract).filter(Contract.is_deleted == False)
    if keyword:
        q = q.filter(
            Contract.contract_no.like(f"%{keyword}%")
        )
    if role == "业务员" and user_id:
        from app.models.user import User
        user = db.query(User).filter(User.id == user_id).first()
        if user:
            q = q.filter(Contract.created_by == (user.display_name or user.username))
    return q.order_by(Contract.id.desc()).options(
        joinedload(Contract.customer),
        joinedload(Contract.spec),
        joinedload(Contract.items).joinedload(ContractItem.spec),
    ).all()


def get_contract(db: Session, id: int):
    return db.query(Contract).filter(
        Contract.id == id, Contract.is_deleted == False
    ).options(
        joinedload(Contract.customer),
        joinedload(Contract.spec),
        joinedload(Contract.items).joinedload(ContractItem.spec),
    ).first()


def create_contract(db: Session, data: ContractCreate, username: str):
    items_data = data.items
    data_dict = data.model_dump(exclude={"items"})
    data_dict["created_by"] = username
    data_dict["updated_by"] = username
    if not data_dict.get("contract_no"):
        data_dict["contract_no"] = generate_contract_no(db)

    contract = Contract(**data_dict)
    db.add(contract)
    db.flush()

    total = 0
    for item_data in items_data:
        item = ContractItem(
            contract_id=contract.id,
            line_no=item_data.line_no,
            spec_id=item_data.spec_id,
            is_pressed=item_data.is_pressed,
            packaging_type=item_data.packaging_type or "",
            delivery_date=item_data.delivery_date,
            pattern_count=item_data.pattern_count or 0,
            pattern_data=item_data.pattern_data,
            unit_price=item_data.unit_price,
            qty=item_data.qty,
            amount=(item_data.unit_price or 0) * (item_data.qty or 0),
            pattern_code=item_data.pattern_code or "",
            color_a=item_data.color_a or "",
            image_a_1=item_data.image_a_1 or "",
            image_a_2=item_data.image_a_2 or "",
            image_a_3=item_data.image_a_3 or "",
            color_b=item_data.color_b or "",
            image_b_1=item_data.image_b_1 or "",
            image_b_2=item_data.image_b_2 or "",
            image_b_3=item_data.image_b_3 or "",
            remark=item_data.remark or "",
        )
        db.add(item)
        total += (item.amount or 0)

    contract.total_amount = total
    db.commit()
    db.refresh(contract)
    return get_contract(db, contract.id)


def update_contract(db: Session, id: int, data: ContractUpdate, username: str):
    contract = get_contract(db, id)
    if not contract:
        return None
    if contract.status == "已下发":
        raise HTTPException(status_code=400, detail="合同已下发，不可修改")
    if contract.is_pushed_down:
        from app.models.process_sheet import ProcessSheet
        sheet = db.query(ProcessSheet).filter(
            ProcessSheet.id == contract.push_down_sheet_id,
            ProcessSheet.is_deleted == False
        ).first()
        if sheet and sheet.status == "已下发":
            raise HTTPException(status_code=400, detail="工艺单已下发，不可修改合同")

    items_data = data.model_dump(exclude_unset=True).pop("items", None)
    for field, value in data.model_dump(exclude_unset=True, exclude={"items"}).items():
        setattr(contract, field, value)

    if items_data is not None:
        db.query(ContractItem).filter(ContractItem.contract_id == id).delete()
        total = 0
        for item_data in items_data:
            item = ContractItem(
                contract_id=id,
                line_no=item_data.line_no,
                spec_id=item_data.spec_id,
                is_pressed=item_data.is_pressed,
                packaging_type=item_data.packaging_type or "",
                delivery_date=item_data.delivery_date,
                pattern_count=item_data.pattern_count or 0,
                pattern_data=item_data.pattern_data,
                unit_price=item_data.unit_price,
                qty=item_data.qty,
                amount=(item_data.unit_price or 0) * (item_data.qty or 0),
                pattern_code=item_data.pattern_code or "",
                color_a=item_data.color_a or "",
                image_a_1=item_data.image_a_1 or "",
                image_a_2=item_data.image_a_2 or "",
                image_a_3=item_data.image_a_3 or "",
                color_b=item_data.color_b or "",
                image_b_1=item_data.image_b_1 or "",
                image_b_2=item_data.image_b_2 or "",
                image_b_3=item_data.image_b_3 or "",
                remark=item_data.remark or "",
            )
            db.add(item)
            total += (item.amount or 0)
        contract.total_amount = total

    contract.updated_by = username
    db.commit()
    db.refresh(contract)
    return get_contract(db, contract.id)


def delete_contract(db: Session, id: int):
    contract = db.query(Contract).filter(Contract.id == id).first()
    if not contract:
        return False
    if contract.status == "已下发":
        raise HTTPException(status_code=400, detail="合同已下发，不可删除")
    contract.is_deleted = True
    db.commit()
    return True


def get_available_contracts(db: Session):
    return db.query(Contract).filter(
        Contract.is_deleted == False,
        Contract.is_pushed_down == False,
        Contract.status == "保存",
    ).options(
        joinedload(Contract.customer),
        joinedload(Contract.spec),
    ).all()


def compute_contract_status(db: Session, contract_id: int) -> str:
    """Derive the display-friendly contract status from its items' production_status."""
    items = db.query(ContractItem).filter(
        ContractItem.contract_id == contract_id
    ).all()
    if not items:
        return "草稿"
    statuses = [i.production_status for i in items]
    all_cancelled = all(s == "cancelled" for s in statuses if s) and any(s for s in statuses)
    all_completed = all(s == "completed" for s in statuses if s) and any(s for s in statuses)
    any_production = any(s and s not in ("cancelled", "completed") for s in statuses)

    if all_cancelled:
        return "已取消"
    if all_completed:
        return "已完成"
    if any_production:
        return "坯布计划已下达"
    return "确认"
