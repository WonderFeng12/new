from datetime import datetime
from sqlalchemy import Column, Integer, String, Text, DECIMAL, ForeignKey
from sqlalchemy.orm import relationship
from app.database import Base


class ContractItem(Base):
    __tablename__ = "contract_item"

    id = Column(Integer, primary_key=True, autoincrement=True)
    contract_id = Column(Integer, ForeignKey("contract.id"), nullable=False)
    line_no = Column(Integer, nullable=False)
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

    contract = relationship("Contract", back_populates="items")
