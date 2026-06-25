from sqlalchemy import Column, Integer, String, ForeignKey, Boolean, Enum as SAEnum
from sqlalchemy.orm import relationship
from app.database import Base
from app.models.mixins import TimestampMixin, SoftDeleteMixin, AuditMixin


class ProcessSheet(Base, TimestampMixin, SoftDeleteMixin, AuditMixin):
    __tablename__ = "process_sheet"

    id = Column(Integer, primary_key=True, autoincrement=True)
    contract_id = Column(Integer, ForeignKey("contract.id"), nullable=False)
    sheet_no = Column(String(100), nullable=False, index=True)
    confirm_version_no = Column(Integer, nullable=False)
    confirm_image_id = Column(Integer, ForeignKey("confirm_image.id"), nullable=True)
    status = Column(SAEnum("草稿", "保存", "已下发"), default="草稿")

    contract = relationship("Contract")
    confirm_image = relationship("ConfirmImage")
