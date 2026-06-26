from sqlalchemy import Column, Integer, String, Text, Enum as SAEnum
from app.database import Base
from app.models.mixins import TimestampMixin, SoftDeleteMixin, AuditMixin

class Spec(Base, TimestampMixin, SoftDeleteMixin, AuditMixin):
    __tablename__ = "spec"

    id = Column(Integer, primary_key=True, autoincrement=True)
    length = Column(String(50), nullable=False, comment="毛毯尺寸-长")
    width = Column(String(50), nullable=False, comment="毛毯尺寸-宽")
    weight = Column(String(50), nullable=False, comment="毛毯重量")
    layer_type = Column(SAEnum("单层", "双层", "复合"), nullable=False)
    splice_method = Column(String(100))
    spec_name = Column(String(200), nullable=False, comment="自动生成: 长*宽/重量/层类型")
    spec_description = Column(Text, comment="自动生成，同 spec_name")
