from sqlalchemy import Column, Integer, String, Text, DECIMAL, Boolean, ForeignKey, Date, JSON
from sqlalchemy.orm import relationship
from app.database import Base


class ProcessSheetItem(Base):
    __tablename__ = "process_sheet_item"

    id = Column(Integer, primary_key=True, autoincrement=True)
    process_sheet_id = Column(Integer, ForeignKey("process_sheet.id"), nullable=False)
    contract_item_id = Column(Integer, ForeignKey("contract_item.id"), nullable=False)
    line_no = Column(Integer, nullable=False)
    spec_id = Column(Integer, ForeignKey("spec.id"), nullable=False)

    # Production detail fields (moved from contract/contract_item)
    is_pressed = Column(Boolean, default=False)
    packaging_type = Column(String(50))
    delivery_date = Column(Date)
    pattern_count = Column(Integer, default=0)
    pattern_data = Column(JSON)
    pattern_code = Column(String(100))
    color_a = Column(String(100))
    image_a_1 = Column(String(500))
    image_a_2 = Column(String(500))
    image_a_3 = Column(String(500))
    color_b = Column(String(100))
    image_b_1 = Column(String(500))
    image_b_2 = Column(String(500))
    image_b_3 = Column(String(500))
    pressed_image = Column(JSON, comment="压花图片URL列表（多图）")
    pressed_image_name = Column(JSON, comment="压花图片原始文件名列表")
    remark = Column(Text)
    process_remark = Column(Text, comment="工艺备注（下推时填写）")
    qty = Column(DECIMAL(12, 2), default=0, comment="数量（从合同行项目带入）")
    cancel_reason = Column(Text, nullable=True)
    cancel_quantities = Column(JSON, nullable=True)

    process_sheet = relationship("ProcessSheet", back_populates="items")
    contract_item = relationship("ContractItem")
    spec = relationship("Spec")
