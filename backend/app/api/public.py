import uuid
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import Optional
from sqlalchemy.orm import Session, joinedload
from app.database import get_db
from app.models.contract import Contract
from app.models.contract_item import ContractItem
from fastapi import Depends

router = APIRouter(prefix="/api/public", tags=["public"])


class ConfirmRequest(BaseModel):
    comment: Optional[str] = ""


@router.get("/contract/{token}")
def get_contract_by_token(token: str, db: Session = Depends(get_db)):
    contract = db.query(Contract).filter(
        Contract.confirm_token == token,
        Contract.is_deleted == False,
    ).options(
        joinedload(Contract.customer),
        joinedload(Contract.items).joinedload(ContractItem.spec),
    ).first()

    if not contract:
        raise HTTPException(status_code=404, detail="无效的确认链接或合同已删除")

    if contract.status != "草稿":
        return {
            "already_confirmed": True,
            "contract_no": contract.contract_no,
            "status": contract.status,
        }

    items_data = []
    for item in contract.items:
        patterns = []
        for p in (item.pattern_data or []):
            patterns.append({
                "code": p.get("code", ""),
                "color": p.get("color", ""),
                "qty": p.get("qty", 0),
                "binding_color_no": p.get("binding_color_no", ""),
                "image": p.get("image", ""),
            })
        items_data.append({
            "line_no": item.line_no,
            "spec_description": item.spec_description or f"规格#{item.spec_id}",
            "is_pressed": item.is_pressed,
            "packaging_type": item.packaging_type or "",
            "delivery_date": str(item.delivery_date) if item.delivery_date else "",
            "pattern_data": patterns,
            "unit_price": float(item.unit_price) if item.unit_price else 0,
            "qty": float(item.qty) if item.qty else 0,
            "amount": float(item.amount) if item.amount else 0,
            "remark": item.remark or "",
        })

    tech_notes = []
    for i in range(1, 11):
        val = getattr(contract, f"tech_note_{i}", None)
        if val:
            tech_notes.append(val)

    return {
        "already_confirmed": False,
        "id": contract.id,
        "contract_no": contract.contract_no,
        "customer_name": contract.customer.name if contract.customer else "",
        "contract_date": str(contract.contract_date),
        "delivery_date": str(contract.delivery_date) if contract.delivery_date else "",
        "binding_material": contract.binding_material or "",
        "binding_width": contract.binding_width or "",
        "binding_color_no": contract.binding_color_no or "",
        "emboss_model": contract.emboss_model or "",
        "total_amount": float(contract.total_amount) if contract.total_amount else 0,
        "tech_notes": tech_notes,
        "pack_notes": [
            getattr(contract, f"pack_note_{i}", "") or ""
            for i in range(1, 6)
        ],
        "box_notes": [
            getattr(contract, f"box_note_{i}", "") or ""
            for i in range(1, 4)
        ],
        "items": items_data,
    }


@router.post("/confirm/{token}")
def confirm_contract_by_token(
    token: str,
    req: ConfirmRequest,
    db: Session = Depends(get_db),
):
    contract = db.query(Contract).filter(
        Contract.confirm_token == token,
        Contract.is_deleted == False,
    ).first()

    if not contract:
        raise HTTPException(status_code=404, detail="无效的确认链接或合同已删除")

    if contract.status != "草稿":
        raise HTTPException(status_code=400, detail="合同已确认，无需重复操作")

    contract.customer_comment = req.comment
    contract.status = "保存"
    from datetime import datetime
    from app.models.confirm_image import ConfirmImage

    latest = db.query(ConfirmImage).filter(
        ConfirmImage.contract_id == contract.id
    ).order_by(ConfirmImage.version_no.desc()).first()
    version_no = (latest.version_no + 1) if latest else 1

    now = datetime.now()
    image = ConfirmImage(
        contract_id=contract.id,
        version_no=version_no,
        generated_by="客户(在线确认)",
        generated_at=now,
        change_log=f"客户在线确认; 意见: {req.comment or '无'}",
        is_confirmed=True,
        confirmed_at=now,
        confirmed_by="客户(在线确认)",
        image_path="",
        contract_snapshot=_contract_to_dict(contract),
    )
    db.add(image)
    contract.latest_confirm_version = version_no
    db.commit()
    return {"message": "确认成功", "contract_no": contract.contract_no}


def _contract_to_dict(contract):
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


# ----- Process Sheet (V2) Public Endpoints -----

@router.get("/process-sheet/{token}")
def get_process_sheet_by_token(
    token: str,
    db: Session = Depends(get_db),
):
    from app.models.process_sheet import ProcessSheet
    from app.models.process_sheet_item import ProcessSheetItem

    sheet = db.query(ProcessSheet).filter(
        ProcessSheet.confirm_token == token,
        ProcessSheet.is_deleted == False,
    ).options(
        joinedload(ProcessSheet.contract),
        joinedload(ProcessSheet.items).joinedload(ProcessSheetItem.spec),
    ).first()

    if not sheet:
        raise HTTPException(status_code=404, detail="确认链接无效或已过期")

    if sheet.status == "已确认":
        return {
            "already_confirmed": True,
            "sheet_no": sheet.sheet_no,
            "status": sheet.status,
        }

    return {
        "already_confirmed": False,
        "id": sheet.id,
        "contract_id": sheet.contract_id,
        "sheet_no": sheet.sheet_no,
        "status": sheet.status,
        "customer_comment": sheet.customer_comment or "",
    }


@router.post("/process-sheet/{token}/confirm")
def confirm_process_sheet(
    token: str,
    req: ConfirmRequest = ConfirmRequest(),
    db: Session = Depends(get_db),
):
    from app.services.process_sheet import customer_confirm_sheet

    result = customer_confirm_sheet(db, token, req.comment or "")
    if result.get("already_confirmed"):
        raise HTTPException(status_code=400, detail="该工艺单已被确认")
    return {"message": "确认成功"}
