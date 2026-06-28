from sqlalchemy import Column, Integer, String, ForeignKey, Boolean, Enum as SAEnum, JSON, Text
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
    status = Column(SAEnum("草稿", "保存", "已下发", "已确认", "修改中"), default="草稿")
    confirm_token = Column(String(36), unique=True, nullable=True)
    customer_comment = Column(Text, nullable=True)

    # Production detail data moved from contract (JSON for flexibility)
    detail_data = Column(JSON, comment="生产详情: tech_notes, accessories, pack_notes, box_notes, binding, emboss etc.")

    contract = relationship("Contract")
    confirm_image = relationship("ConfirmImage")
    items = relationship("ProcessSheetItem", back_populates="process_sheet", cascade="all, delete-orphan")
