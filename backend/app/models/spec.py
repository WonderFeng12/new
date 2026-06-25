from sqlalchemy import Column, Integer, String, Text, Enum as SAEnum
from app.database import Base
from app.models.mixins import TimestampMixin, SoftDeleteMixin, AuditMixin

class Spec(Base, TimestampMixin, SoftDeleteMixin, AuditMixin):
    __tablename__ = "spec"

    id = Column(Integer, primary_key=True, autoincrement=True)
    spec_name = Column(String(100), nullable=False)
    weight = Column(String(50), nullable=False)
    layer_type = Column(SAEnum("单层", "双层", "复合"), nullable=False)
    splice_method = Column(String(100))
    spec_description = Column(Text)
