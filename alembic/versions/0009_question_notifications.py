"""add n8n notification state to product questions

Revision ID: 0009_question_notifications
Revises: 0008_ingestion_change_metrics
"""

from alembic import op
import sqlalchemy as sa


revision = "0009_question_notifications"
down_revision = "0008_ingestion_change_metrics"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column(
        "questions",
        sa.Column("notification_attempts", sa.Integer(), nullable=False, server_default="0"),
        schema="product",
    )
    op.add_column(
        "questions",
        sa.Column("notified_at", sa.DateTime(timezone=True)),
        schema="product",
    )
    op.add_column(
        "questions",
        sa.Column("last_notification_error", sa.Text()),
        schema="product",
    )
    op.create_index(
        "ix_product_questions_notification_queue",
        "questions",
        ["status", "notification_attempts", "created_at"],
        schema="product",
    )


def downgrade() -> None:
    op.drop_index(
        "ix_product_questions_notification_queue",
        table_name="questions",
        schema="product",
    )
    op.drop_column("questions", "last_notification_error", schema="product")
    op.drop_column("questions", "notified_at", schema="product")
    op.drop_column("questions", "notification_attempts", schema="product")
