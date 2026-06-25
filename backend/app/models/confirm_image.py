from datetime import datetime
from sqlalchemy import Column, Integer, String, Text, DateTime, Boolean, JSON, ForeignKey
from app.database import Base


class ConfirmImage(Base):
    __tablename__ = "confirm_image"

    id = Column(Integer, primary_key=True, autoincrement=True)
    contract_id = Column(Integer, ForeignKey("contract.id"), nullable=False)
    version_no = Column(Integer, nullable=False)
    generated_at = Column(DateTime, default=datetime.now)
    generated_by = Column(String(100))
    change_log = Column(Text)
    is_confirmed = Column(Boolean, default=False)
    confirmed_at = Column(DateTime, nullable=True)
    confirmed_by = Column(String(100), nullable=True)
    image_path = Column(String(500))
    contract_snapshot = Column(JSON)
