"""add ingestion change metrics

Revision ID: 0008_ingestion_change_metrics
Revises: 0007_seed_mortgage_tedr
"""

from alembic import op
import sqlalchemy as sa


revision = "0008_ingestion_change_metrics"
down_revision = "0007_seed_mortgage_tedr"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column(
        "ingestion_runs",
        sa.Column("rows_inserted", sa.Integer(), nullable=False, server_default="0"),
        schema="control",
    )
    op.add_column(
        "ingestion_runs",
        sa.Column("rows_updated", sa.Integer(), nullable=False, server_default="0"),
        schema="control",
    )
    op.add_column(
        "ingestion_runs",
        sa.Column("rows_unchanged", sa.Integer(), nullable=False, server_default="0"),
        schema="control",
    )
    op.add_column(
        "ingestion_runs",
        sa.Column("latest_period", sa.Date(), nullable=True),
        schema="control",
    )


def downgrade() -> None:
    op.drop_column("ingestion_runs", "latest_period", schema="control")
    op.drop_column("ingestion_runs", "rows_unchanged", schema="control")
    op.drop_column("ingestion_runs", "rows_updated", schema="control")
    op.drop_column("ingestion_runs", "rows_inserted", schema="control")
