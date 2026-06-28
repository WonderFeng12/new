from sqlalchemy import Column, Integer, String, Text
from app.database import Base
from app.models.mixins import TimestampMixin


class BasicData(Base, TimestampMixin):
    __tablename__ = "basic_data"

    id = Column(Integer, primary_key=True, autoincrement=True)
    category = Column(String(50), nullable=False, index=True, comment="分类: color, packing, layer_type, code_rules")
    code = Column(String(100), nullable=False, comment="代码/键")
    value = Column(String(200), comment="值")
    sort_order = Column(Integer, default=0)
