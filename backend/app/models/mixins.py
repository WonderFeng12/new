from datetime import datetime
from sqlalchemy import Column, String, DateTime, Boolean


class TimestampMixin:
    created_at = Column(DateTime, default=datetime.now)
    updated_at = Column(DateTime, default=datetime.now, onupdate=datetime.now)


class SoftDeleteMixin:
    is_deleted = Column(Boolean, default=False)


class AuditMixin:
    created_by = Column(String(100), nullable=True)
    updated_by = Column(String(100), nullable=True)
