from sqlalchemy import Column, Integer, String, ForeignKey, Boolean, Enum as SAEnum, JSON, Text, DECIMAL
from sqlalchemy.orm import relationship
from app.database import Base
from app.models.mixins import TimestampMixin, SoftDeleteMixin, AuditMixin


class ProcessSheet(Base, TimestampMixin, SoftDeleteMixin, AuditMixin):
    __tablename__ = "process_sheet"

    id = Column(Integer, primary_key=True, autoincrement=True)
    contract_id = Column(Integer, ForeignKey("contract.id"), nullable=False)
    sheet_no = Column(String(100), nullable=False, index=True)
    confirm_version_no = Column(DECIMAL(10, 2), nullable=False, default=0)
    confirm_image_id = Column(Integer, ForeignKey("confirm_image.id"), nullable=True)
    status = Column(SAEnum("草稿", "保存", "已下发", "已确认", "修改中"), default="草稿")
    confirm_token = Column(String(36), unique=True, nullable=True)
    customer_comment = Column(Text, nullable=True)
    version_marked = Column(Boolean, default=False, comment="是否已标记版本用于客户沟通")
    version_note = Column(Text, nullable=True, comment="版本标记说明（更改原因）")
    customer_confirmed = Column(Boolean, default=False, comment="客户是否已确认")
    internal_confirm_required = Column(Integer, default=1, comment="内部确认所需人数（保留向后兼容，实际以名单为准）")
    internal_confirmed_users = Column(JSON, default=[], comment="已内部确认的用户ID列表")
    confirm_user_ids = Column(JSON, default=[], comment="工艺单指定的内部确认人用户ID列表，新建时从系统配置继承")

    # Production detail data moved from contract (JSON for flexibility)
    detail_data = Column(JSON, comment="生产详情: tech_notes, accessories, pack_notes, box_notes, binding, emboss etc.")
    contract_snapshot = Column(JSON, comment="下推时的合同数据快照，用于对比版本差异")

    contract = relationship("Contract")
    confirm_image = relationship("ConfirmImage")
    items = relationship("ProcessSheetItem", back_populates="process_sheet", cascade="all, delete-orphan")
