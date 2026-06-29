from datetime import datetime
from sqlalchemy import Column, Integer, String, Text, DateTime, Enum, ForeignKey, Index
from sqlalchemy.orm import relationship
from app.database import Base


class ProductionLog(Base):
    __tablename__ = "production_log"

    id = Column(Integer, primary_key=True, autoincrement=True)
    contract_id = Column(Integer, ForeignKey("contract.id"), nullable=False)
    contract_item_id = Column(Integer, ForeignKey("contract_item.id"), nullable=True)
    from_status = Column(String(30), nullable=True)
    to_status = Column(String(30), nullable=False)
    operation_type = Column(Enum("推进", "回退", "返工", "取消", "确认", "坯布下达", "重新编辑"), nullable=False)
    operator_id = Column(Integer, ForeignKey("user.id"), nullable=True)
    remark = Column(Text, nullable=True)
    created_at = Column(DateTime, default=datetime.now)
    notify_status = Column(String(20), default="pending")

    __table_args__ = (
        Index("idx_item_log", "contract_item_id", "created_at"),
        Index("idx_contract_log", "contract_id", "created_at"),
    )

    contract = relationship("Contract")
    contract_item = relationship("ContractItem")
    operator = relationship("User")
