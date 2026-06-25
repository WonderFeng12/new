from datetime import datetime
from typing import Any
from sqlalchemy.orm import Session
from fastapi import HTTPException
from app.models.contract import Contract
from app.models.confirm_image import ConfirmImage
from app.schemas.contract import ContractOut


def get_versions(db: Session, contract_id: int):
    return db.query(ConfirmImage).filter(
        ConfirmImage.contract_id == contract_id
    ).order_by(ConfirmImage.version_no.desc()).all()


def get_latest(db: Session, contract_id: int):
    return db.query(ConfirmImage).filter(
        ConfirmImage.contract_id == contract_id
    ).order_by(ConfirmImage.version_no.desc()).first()


def generate_confirm_image(db: Session, contract_id: int, username: str, image_path: str = ""):
    contract = db.query(Contract).filter(Contract.id == contract_id).first()
    if not contract or contract.is_deleted:
        raise HTTPException(status_code=404, detail="合同不存在")

    last = get_latest(db, contract_id)
    version_no = (last.version_no + 1) if last else 1

    change_parts = []
    if last and last.contract_snapshot:
        old = last.contract_snapshot
        new = _contract_to_dict(contract)
        if old.get("total_amount") != new.get("total_amount"):
            change_parts.append(f"金额变更: {old.get('total_amount')} → {new.get('total_amount')}")
        old_items = {(i.get("line_no"), i.get("pattern_code")) for i in old.get("items", [])}
        new_items = {(i.get("line_no"), i.get("pattern_code")) for i in new.get("items", [])}
        if old_items != new_items:
            change_parts.append(f"花型行项目变更")
        if not change_parts:
            change_parts.append("其他信息变更")
    else:
        change_parts.append("首次生成")

    now = datetime.now()
    image_record = ConfirmImage(
        contract_id=contract_id,
        version_no=version_no,
        generated_by=username,
        generated_at=now,
        change_log="; ".join(change_parts),
        is_confirmed=False,
        image_path=image_path,
        contract_snapshot=_contract_to_dict(contract),
    )
    db.add(image_record)
    contract.latest_confirm_version = version_no
    db.commit()
    db.refresh(image_record)
    return image_record


def mark_confirmed(db: Session, contract_id: int, username: str):
    contract = db.query(Contract).filter(Contract.id == contract_id).first()
    if not contract or contract.is_deleted:
        raise HTTPException(status_code=404, detail="合同不存在")
    if contract.status != "草稿":
        raise HTTPException(status_code=400, detail="合同已确认，无需重复操作")

    latest = get_latest(db, contract_id)
    if not latest:
        raise HTTPException(status_code=400, detail="请先生成确认图")

    latest.is_confirmed = True
    latest.confirmed_at = datetime.now()
    latest.confirmed_by = username
    contract.status = "保存"
    db.commit()
    return latest


def _contract_to_dict(contract: Contract) -> dict[str, Any]:
    return {
        "id": contract.id,
        "contract_no": contract.contract_no,
        "spec_description": contract.spec_description,
        "total_amount": float(contract.total_amount) if contract.total_amount else 0,
        "items": [
            {
                "line_no": i.line_no,
                "pattern_code": i.pattern_code,
                "unit_price": float(i.unit_price) if i.unit_price else 0,
                "qty": float(i.qty) if i.qty else 0,
                "amount": float(i.amount) if i.amount else 0,
            }
            for i in contract.items
        ],
    }
