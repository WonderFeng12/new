from sqlalchemy import Column, Integer, String, Text
from app.database import Base
from app.models.mixins import TimestampMixin, SoftDeleteMixin, AuditMixin

class Customer(Base, TimestampMixin, SoftDeleteMixin, AuditMixin):
    __tablename__ = "customer"

    id = Column(Integer, primary_key=True, autoincrement=True)
    customer_no = Column(String(50), unique=True, index=True)
    name = Column(String(200), nullable=False)
    contact = Column(String(100))
    phone = Column(String(50))
    address = Column(Text)
