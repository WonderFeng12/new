from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import Optional
from sqlalchemy.orm import Session, joinedload
from app.database import get_db
from fastapi import Depends

router = APIRouter(prefix="/api/public", tags=["public"])


class ConfirmRequest(BaseModel):
    comment: Optional[str] = ""


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

    contract = sheet.contract
    items_data = []
    for item in sheet.items:
        items_data.append({
            "line_no": item.line_no,
            "spec_description": item.spec.spec_name if item.spec else f"规格#{item.spec_id}",
            "spec_id": item.spec_id,
            "is_pressed": item.is_pressed,
            "packaging_type": item.packaging_type or "",
            "delivery_date": str(item.delivery_date) if item.delivery_date else "",
            "pattern_count": item.pattern_count or 0,
            "pattern_data": item.pattern_data,
            "pattern_code": item.pattern_code or "",
            "color_a": item.color_a or "",
            "color_b": item.color_b or "",
            "image_a_1": item.image_a_1 or "",
            "image_a_2": item.image_a_2 or "",
            "image_a_3": item.image_a_3 or "",
            "image_b_1": item.image_b_1 or "",
            "image_b_2": item.image_b_2 or "",
            "image_b_3": item.image_b_3 or "",
            "qty": float(item.qty) if item.qty else 0,
            "process_remark": item.process_remark or "",
            "remark": item.remark or "",
        })

    return {
        "already_confirmed": False,
        "id": sheet.id,
        "contract_id": sheet.contract_id,
        "sheet_no": sheet.sheet_no,
        "confirm_version_no": float(sheet.confirm_version_no or 0),
        "status": sheet.status,
        "customer_comment": sheet.customer_comment or "",
        "contract_contract_no": contract.contract_no if contract else "",
        "contract_customer_name": contract.customer.name if contract and contract.customer else "",
        "contract_date": str(contract.contract_date) if contract and contract.contract_date else "",
        "items": items_data,
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
