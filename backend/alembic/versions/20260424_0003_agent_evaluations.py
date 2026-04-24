"""agent evaluations

Revision ID: 20260424_0003
Revises: 20260423_0002
Create Date: 2026-04-24 00:00:00
"""

import sqlalchemy as sa

from alembic import op

# revision identifiers, used by Alembic.
revision = "20260424_0003"
down_revision = "20260423_0002"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "agent_evaluations",
        sa.Column("id", sa.String(), nullable=False),
        sa.Column("workflow_step_attempt_id", sa.String(), nullable=False),
        sa.Column("workflow_step_id", sa.String(), nullable=False),
        sa.Column("application_id", sa.String(), nullable=False),
        sa.Column("agent_name", sa.String(), nullable=False),
        sa.Column("status", sa.String(), nullable=False),
        sa.Column("schema_valid", sa.Boolean(), nullable=False),
        sa.Column("guardrail_adjusted", sa.Boolean(), nullable=False),
        sa.Column("score", sa.Float(), nullable=True),
        sa.Column("confidence", sa.Float(), nullable=True),
        sa.Column("decision", sa.String(), nullable=True),
        sa.Column("final_decision", sa.String(), nullable=True),
        sa.Column("flags_count", sa.Integer(), nullable=False),
        sa.Column("tool_evidence_count", sa.Integer(), nullable=False),
        sa.Column("completed_tool_evidence_count", sa.Integer(), nullable=False),
        sa.Column("latency_ms", sa.Integer(), nullable=True),
        sa.Column("model_provider", sa.String(), nullable=True),
        sa.Column("model_name", sa.String(), nullable=True),
        sa.Column("prompt_version", sa.String(), nullable=True),
        sa.Column("supports_mcp", sa.Boolean(), nullable=False),
        sa.Column("evaluation_json", sa.Text(), nullable=False),
        sa.Column("error_message", sa.Text(), nullable=True),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(["application_id"], ["applications.id"]),
        sa.ForeignKeyConstraint(
            ["workflow_step_attempt_id"], ["workflow_step_attempts.id"]
        ),
        sa.ForeignKeyConstraint(["workflow_step_id"], ["workflow_steps.id"]),
        sa.PrimaryKeyConstraint("id"),
    )


def downgrade() -> None:
    op.drop_table("agent_evaluations")
