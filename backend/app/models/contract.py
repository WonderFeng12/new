from datetime import datetime
from sqlalchemy import Column, Integer, String, Text, Date, DateTime, DECIMAL, Boolean, ForeignKey, Enum as SAEnum
from sqlalchemy.orm import relationship
from app.database import Base
from app.models.mixins import TimestampMixin, SoftDeleteMixin, AuditMixin


class Contract(Base, TimestampMixin, SoftDeleteMixin, AuditMixin):
    __tablename__ = "contract"

    id = Column(Integer, primary_key=True, autoincrement=True)
    contract_no = Column(String(100), nullable=False, index=True)
    customer_id = Column(Integer, ForeignKey("customer.id"), nullable=False)
    contract_date = Column(Date, nullable=False)
    spec_id = Column(Integer, ForeignKey("spec.id"), nullable=False)
    spec_description = Column(Text)
    is_pressed = Column(Boolean, default=False)
    packaging_type = Column(String(50))
    delivery_date = Column(Date)

    binding_material = Column(String(200))
    binding_width = Column(String(50))
    binding_color_no = Column(String(50))

    tech_note_1 = Column(Text)
    tech_note_2 = Column(Text)
    tech_note_3 = Column(Text)
    tech_note_4 = Column(Text)
    tech_note_5 = Column(Text)
    tech_note_6 = Column(Text)
    tech_note_7 = Column(Text)
    tech_note_8 = Column(Text)
    tech_note_9 = Column(Text)
    tech_note_10 = Column(Text)

    accessory_desc_1 = Column(String(200))
    accessory_size_1 = Column(String(100))
    accessory_qty_1 = Column(DECIMAL(10, 2))
    accessory_desc_2 = Column(String(200))
    accessory_size_2 = Column(String(100))
    accessory_qty_2 = Column(DECIMAL(10, 2))
    accessory_desc_3 = Column(String(200))
    accessory_size_3 = Column(String(100))
    accessory_qty_3 = Column(DECIMAL(10, 2))
    accessory_desc_4 = Column(String(200))
    accessory_size_4 = Column(String(100))
    accessory_qty_4 = Column(DECIMAL(10, 2))
    accessory_desc_5 = Column(String(200))
    accessory_size_5 = Column(String(100))
    accessory_qty_5 = Column(DECIMAL(10, 2))
    accessory_desc_6 = Column(String(200))
    accessory_size_6 = Column(String(100))
    accessory_qty_6 = Column(DECIMAL(10, 2))

    pack_note_1 = Column(Text)
    pack_note_2 = Column(Text)
    pack_note_3 = Column(Text)
    pack_note_4 = Column(Text)
    pack_note_5 = Column(Text)

    box_note_1 = Column(Text)
    box_note_2 = Column(Text)
    box_note_3 = Column(Text)

    emboss_model = Column(String(100))
    total_amount = Column(DECIMAL(12, 2))

    status = Column(SAEnum("草稿", "保存", "已下发"), default="草稿")
    is_pushed_down = Column(Boolean, default=False)
    push_down_sheet_id = Column(Integer, nullable=True)
    latest_confirm_version = Column(Integer, default=0)

    customer = relationship("Customer")
    spec = relationship("Spec")
    items = relationship("ContractItem", back_populates="contract", cascade="all, delete-orphan")
