from datetime import datetime
from sqlalchemy import Column, Integer, String, Text, DECIMAL, Boolean, ForeignKey, Date, JSON
from sqlalchemy.orm import relationship
from app.database import Base


class ContractItem(Base):
    __tablename__ = "contract_item"

    id = Column(Integer, primary_key=True, autoincrement=True)
    contract_id = Column(Integer, ForeignKey("contract.id"), nullable=False)
    line_no = Column(Integer, nullable=False)
    spec_id = Column(Integer, ForeignKey("spec.id"), nullable=False)
    is_pressed = Column(Boolean, default=False)
    packaging_type = Column(String(50))
    delivery_date = Column(Date)
    pattern_count = Column(Integer, default=0)
    pattern_data = Column(JSON)
    unit_price = Column(DECIMAL(10, 2))
    qty = Column(DECIMAL(10, 2))
    amount = Column(DECIMAL(12, 2))
    pattern_code = Column(String(100))
    color_a = Column(String(100))
    image_a_1 = Column(String(500))
    image_a_2 = Column(String(500))
    image_a_3 = Column(String(500))
    color_b = Column(String(100))
    image_b_1 = Column(String(500))
    image_b_2 = Column(String(500))
    image_b_3 = Column(String(500))
    remark = Column(Text)
    production_status = Column(String(30), nullable=True)
    yarn_plan_user_id = Column(Integer, ForeignKey("user.id"), nullable=True)
    cancel_quantities = Column(JSON, nullable=True)
    cancel_reason = Column(Text, nullable=True)

    spec = relationship("Spec")
    contract = relationship("Contract", back_populates="items")

    @property
    def spec_description(self):
        return self.spec.spec_description if self.spec else None
