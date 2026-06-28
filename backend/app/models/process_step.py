from datetime import datetime
from sqlalchemy import Column, Integer, String, Boolean, DateTime
from sqlalchemy.orm import relationship
from app.database import Base


class ProcessStep(Base):
    __tablename__ = "process_step"

    id = Column(Integer, primary_key=True, autoincrement=True)
    step_code = Column(String(30), unique=True, nullable=False)
    step_name = Column(String(50), nullable=False)
    sort_order = Column(Integer, nullable=False, default=0)
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.now)

    assignees = relationship("ProcessStepAssignee", back_populates="process_step")
