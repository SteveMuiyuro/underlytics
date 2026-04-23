from uuid import uuid4

from sqlalchemy import ForeignKey, String
from sqlalchemy.orm import Mapped, mapped_column

from underlytics_api.models.base import Base


class WorkflowStepDependency(Base):
    __tablename__ = "workflow_step_dependencies"

    id: Mapped[str] = mapped_column(String, primary_key=True, default=lambda: str(uuid4()))
    workflow_step_id: Mapped[str] = mapped_column(
        String, ForeignKey("workflow_steps.id"), nullable=False
    )
    depends_on_step_id: Mapped[str] = mapped_column(
        String, ForeignKey("workflow_steps.id"), nullable=False
    )
