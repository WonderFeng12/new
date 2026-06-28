from datetime import datetime
from sqlalchemy import Column, Integer, DateTime, ForeignKey, UniqueConstraint
from sqlalchemy.orm import relationship
from app.database import Base


class ProcessStepAssignee(Base):
    __tablename__ = "process_step_assignee"

    id = Column(Integer, primary_key=True, autoincrement=True)
    process_step_id = Column(Integer, ForeignKey("process_step.id"), nullable=False)
    user_id = Column(Integer, ForeignKey("user.id"), nullable=False)
    created_at = Column(DateTime, default=datetime.now)

    __table_args__ = (
        UniqueConstraint("process_step_id", "user_id", name="uq_step_user"),
    )

    process_step = relationship("ProcessStep", back_populates="assignees")
    user = relationship("User")
