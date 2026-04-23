"""orchestration foundation

Revision ID: 20260422_0001
Revises:
Create Date: 2026-04-22 00:00:00
"""

import sqlalchemy as sa

from alembic import op

# revision identifiers, used by Alembic.
revision = "20260422_0001"
down_revision = None
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "users",
        sa.Column("id", sa.String(), nullable=False),
        sa.Column("clerk_user_id", sa.String(), nullable=False),
        sa.Column("role", sa.String(), nullable=False),
        sa.Column("email", sa.String(), nullable=False),
        sa.Column("full_name", sa.String(), nullable=False),
        sa.Column("phone_number", sa.String(), nullable=True),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.Column("updated_at", sa.DateTime(), nullable=False),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("clerk_user_id"),
        sa.UniqueConstraint("email"),
    )
    op.create_table(
        "loan_products",
        sa.Column("id", sa.String(), nullable=False),
        sa.Column("code", sa.String(), nullable=False),
        sa.Column("name", sa.String(), nullable=False),
        sa.Column("description", sa.String(), nullable=True),
        sa.Column("min_amount", sa.Integer(), nullable=False),
        sa.Column("max_amount", sa.Integer(), nullable=False),
        sa.Column("min_term_months", sa.Integer(), nullable=False),
        sa.Column("max_term_months", sa.Integer(), nullable=False),
        sa.Column("is_active", sa.Boolean(), nullable=False),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.Column("updated_at", sa.DateTime(), nullable=False),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("code"),
    )
    op.create_table(
        "applications",
        sa.Column("id", sa.String(), nullable=False),
        sa.Column("application_number", sa.String(), nullable=False),
        sa.Column("applicant_user_id", sa.String(), nullable=False),
        sa.Column("loan_product_id", sa.String(), nullable=False),
        sa.Column("status", sa.String(), nullable=False),
        sa.Column("requested_amount", sa.Integer(), nullable=False),
        sa.Column("requested_term_months", sa.Integer(), nullable=False),
        sa.Column("loan_purpose", sa.Text(), nullable=True),
        sa.Column("monthly_income", sa.Integer(), nullable=False),
        sa.Column("monthly_expenses", sa.Integer(), nullable=False),
        sa.Column("existing_loan_obligations", sa.Integer(), nullable=False),
        sa.Column("employment_status", sa.String(), nullable=True),
        sa.Column("employer_name", sa.String(), nullable=True),
        sa.Column("bank_name", sa.String(), nullable=True),
        sa.Column("account_type", sa.String(), nullable=True),
        sa.Column("submitted_at", sa.DateTime(), nullable=True),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.Column("updated_at", sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(["applicant_user_id"], ["users.id"]),
        sa.ForeignKeyConstraint(["loan_product_id"], ["loan_products.id"]),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("application_number"),
    )
    op.create_table(
        "application_documents",
        sa.Column("id", sa.String(), nullable=False),
        sa.Column("application_id", sa.String(), nullable=False),
        sa.Column("document_type", sa.String(), nullable=False),
        sa.Column("file_name", sa.String(), nullable=False),
        sa.Column("file_path", sa.String(), nullable=False),
        sa.Column("mime_type", sa.String(), nullable=False),
        sa.Column("file_size_bytes", sa.Integer(), nullable=False),
        sa.Column("upload_status", sa.String(), nullable=False),
        sa.Column("is_required", sa.Boolean(), nullable=False),
        sa.Column("uploaded_at", sa.DateTime(), nullable=False),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.Column("updated_at", sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(["application_id"], ["applications.id"]),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_table(
        "underwriting_jobs",
        sa.Column("id", sa.String(), nullable=False),
        sa.Column("application_id", sa.String(), nullable=False),
        sa.Column("status", sa.String(), nullable=False),
        sa.Column("current_step", sa.String(), nullable=True),
        sa.Column("started_at", sa.DateTime(), nullable=True),
        sa.Column("completed_at", sa.DateTime(), nullable=True),
        sa.Column("failed_at", sa.DateTime(), nullable=True),
        sa.Column("retry_count", sa.Integer(), nullable=False),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.Column("updated_at", sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(["application_id"], ["applications.id"]),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_table(
        "agent_runs",
        sa.Column("id", sa.String(), nullable=False),
        sa.Column("underwriting_job_id", sa.String(), nullable=False),
        sa.Column("application_id", sa.String(), nullable=False),
        sa.Column("agent_name", sa.String(), nullable=False),
        sa.Column("status", sa.String(), nullable=False),
        sa.Column("started_at", sa.DateTime(), nullable=True),
        sa.Column("completed_at", sa.DateTime(), nullable=True),
        sa.Column("failed_at", sa.DateTime(), nullable=True),
        sa.Column("retry_count", sa.Integer(), nullable=False),
        sa.Column("error_message", sa.Text(), nullable=True),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.Column("updated_at", sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(["application_id"], ["applications.id"]),
        sa.ForeignKeyConstraint(["underwriting_job_id"], ["underwriting_jobs.id"]),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_table(
        "agent_outputs",
        sa.Column("id", sa.String(), nullable=False),
        sa.Column("agent_run_id", sa.String(), nullable=False),
        sa.Column("application_id", sa.String(), nullable=False),
        sa.Column("agent_name", sa.String(), nullable=False),
        sa.Column("score", sa.Float(), nullable=True),
        sa.Column("confidence", sa.Float(), nullable=True),
        sa.Column("decision", sa.String(), nullable=True),
        sa.Column("flags", sa.Text(), nullable=True),
        sa.Column("reasoning", sa.Text(), nullable=True),
        sa.Column("output_json", sa.Text(), nullable=False),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.Column("updated_at", sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(["agent_run_id"], ["agent_runs.id"]),
        sa.ForeignKeyConstraint(["application_id"], ["applications.id"]),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_table(
        "workflow_plans",
        sa.Column("id", sa.String(), nullable=False),
        sa.Column("application_id", sa.String(), nullable=False),
        sa.Column("plan_version", sa.String(), nullable=False),
        sa.Column("planner_mode", sa.String(), nullable=False),
        sa.Column("status", sa.String(), nullable=False),
        sa.Column("summary", sa.Text(), nullable=True),
        sa.Column("plan_json", sa.Text(), nullable=False),
        sa.Column("trace_id", sa.String(), nullable=True),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.Column("updated_at", sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(["application_id"], ["applications.id"]),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_table(
        "workflow_steps",
        sa.Column("id", sa.String(), nullable=False),
        sa.Column("workflow_plan_id", sa.String(), nullable=False),
        sa.Column("application_id", sa.String(), nullable=False),
        sa.Column("step_key", sa.String(), nullable=False),
        sa.Column("step_type", sa.String(), nullable=False),
        sa.Column("worker_name", sa.String(), nullable=False),
        sa.Column("status", sa.String(), nullable=False),
        sa.Column("queue_name", sa.String(), nullable=True),
        sa.Column("input_context_json", sa.Text(), nullable=False),
        sa.Column("output_schema_version", sa.String(), nullable=False),
        sa.Column("decision", sa.String(), nullable=True),
        sa.Column("priority", sa.Integer(), nullable=False),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.Column("updated_at", sa.DateTime(), nullable=False),
        sa.Column("started_at", sa.DateTime(), nullable=True),
        sa.Column("completed_at", sa.DateTime(), nullable=True),
        sa.Column("failed_at", sa.DateTime(), nullable=True),
        sa.ForeignKeyConstraint(["application_id"], ["applications.id"]),
        sa.ForeignKeyConstraint(["workflow_plan_id"], ["workflow_plans.id"]),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_table(
        "workflow_step_dependencies",
        sa.Column("id", sa.String(), nullable=False),
        sa.Column("workflow_step_id", sa.String(), nullable=False),
        sa.Column("depends_on_step_id", sa.String(), nullable=False),
        sa.ForeignKeyConstraint(["depends_on_step_id"], ["workflow_steps.id"]),
        sa.ForeignKeyConstraint(["workflow_step_id"], ["workflow_steps.id"]),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_table(
        "workflow_step_attempts",
        sa.Column("id", sa.String(), nullable=False),
        sa.Column("workflow_step_id", sa.String(), nullable=False),
        sa.Column("attempt_number", sa.Integer(), nullable=False),
        sa.Column("executor_type", sa.String(), nullable=False),
        sa.Column("model_name", sa.String(), nullable=True),
        sa.Column("status", sa.String(), nullable=False),
        sa.Column("error_message", sa.Text(), nullable=True),
        sa.Column("trace_id", sa.String(), nullable=True),
        sa.Column("started_at", sa.DateTime(), nullable=True),
        sa.Column("completed_at", sa.DateTime(), nullable=True),
        sa.ForeignKeyConstraint(["workflow_step_id"], ["workflow_steps.id"]),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_table(
        "manual_review_cases",
        sa.Column("id", sa.String(), nullable=False),
        sa.Column("application_id", sa.String(), nullable=False),
        sa.Column("workflow_plan_id", sa.String(), nullable=False),
        sa.Column("status", sa.String(), nullable=False),
        sa.Column("reason", sa.Text(), nullable=False),
        sa.Column("assigned_reviewer_user_id", sa.String(), nullable=True),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.Column("resolved_at", sa.DateTime(), nullable=True),
        sa.ForeignKeyConstraint(["application_id"], ["applications.id"]),
        sa.ForeignKeyConstraint(["assigned_reviewer_user_id"], ["users.id"]),
        sa.ForeignKeyConstraint(["workflow_plan_id"], ["workflow_plans.id"]),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_table(
        "manual_review_actions",
        sa.Column("id", sa.String(), nullable=False),
        sa.Column("manual_review_case_id", sa.String(), nullable=False),
        sa.Column("reviewer_user_id", sa.String(), nullable=False),
        sa.Column("action", sa.String(), nullable=False),
        sa.Column("note", sa.Text(), nullable=False),
        sa.Column("old_decision", sa.String(), nullable=True),
        sa.Column("new_decision", sa.String(), nullable=True),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(
            ["manual_review_case_id"], ["manual_review_cases.id"]
        ),
        sa.ForeignKeyConstraint(["reviewer_user_id"], ["users.id"]),
        sa.PrimaryKeyConstraint("id"),
    )


def downgrade() -> None:
    op.drop_table("manual_review_actions")
    op.drop_table("manual_review_cases")
    op.drop_table("workflow_step_attempts")
    op.drop_table("workflow_step_dependencies")
    op.drop_table("workflow_steps")
    op.drop_table("workflow_plans")
    op.drop_table("agent_outputs")
    op.drop_table("agent_runs")
    op.drop_table("underwriting_jobs")
    op.drop_table("application_documents")
    op.drop_table("applications")
    op.drop_table("loan_products")
    op.drop_table("users")
