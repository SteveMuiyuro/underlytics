"""add phone_number to applications

Revision ID: 4babb38a3e3a
Revises: 20260424_0003
Create Date: 2026-04-26
"""
from alembic import op
import sqlalchemy as sa


# revision identifiers
revision = "4babb38a3e3a"
down_revision = "20260424_0003"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column(
        "applications",
        sa.Column("phone_number", sa.String(), nullable=True),
    )


def downgrade() -> None:
    op.drop_column("applications", "phone_number")