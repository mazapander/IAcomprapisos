"""add consented product analytics and questions

Revision ID: 0006_product_analytics
Revises: 0005_seed_income_mortgage_market
"""

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

revision = "0006_product_analytics"
down_revision = "0005_seed_income_mortgage_market"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.execute("CREATE SCHEMA IF NOT EXISTS product")
    op.create_table(
        "visitors",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("consent_version", sa.String(20), nullable=False),
        sa.Column("consented_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("last_seen_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("expires_at", sa.DateTime(timezone=True), nullable=False),
        schema="product",
    )
    op.create_index("ix_product_visitors_last_seen", "visitors", ["last_seen_at"], schema="product")
    op.create_table(
        "events",
        sa.Column("id", sa.BigInteger(), primary_key=True, autoincrement=True),
        sa.Column("visitor_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("session_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("event_name", sa.String(50), nullable=False),
        sa.Column("page_path", sa.String(200), nullable=False),
        sa.Column("properties", postgresql.JSONB(), nullable=False, server_default=sa.text("'{}'::jsonb")),
        sa.Column("occurred_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("expires_at", sa.DateTime(timezone=True), nullable=False),
        schema="product",
    )
    op.create_index("ix_product_events_name_occurred", "events", ["event_name", "occurred_at"], schema="product")
    op.create_index("ix_product_events_visitor_occurred", "events", ["visitor_id", "occurred_at"], schema="product")
    op.create_table(
        "questions",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("visitor_id", postgresql.UUID(as_uuid=True)),
        sa.Column("question", sa.Text(), nullable=False),
        sa.Column("category", sa.String(40), nullable=False),
        sa.Column("journey_stage", sa.String(40), nullable=False),
        sa.Column("geography_code", sa.String(20)),
        sa.Column("contact_email", sa.String(254)),
        sa.Column("contact_consent", sa.Boolean(), nullable=False, server_default=sa.false()),
        sa.Column("privacy_notice_version", sa.String(20), nullable=False),
        sa.Column("status", sa.String(20), nullable=False, server_default="new"),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("expires_at", sa.DateTime(timezone=True), nullable=False),
        schema="product",
    )
    op.create_index("ix_product_questions_status_created", "questions", ["status", "created_at"], schema="product")


def downgrade() -> None:
    op.drop_schema("product", cascade=True)
