"""store consented user market observations

Revision ID: 0010_market_observations
Revises: 0009_question_notifications
"""

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql


revision = "0010_market_observations"
down_revision = "0009_question_notifications"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "market_observations",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("geography_code", sa.String(20), nullable=False),
        sa.Column("property_type", sa.String(20), nullable=False),
        sa.Column("property_age", sa.String(20), nullable=False),
        sa.Column("contributor_role", sa.String(20), nullable=False),
        sa.Column("surface_area_m2", sa.Numeric(8, 2), nullable=False),
        sa.Column("asking_price_eur", sa.Numeric(14, 2)),
        sa.Column("appraisal_value_eur", sa.Numeric(14, 2)),
        sa.Column("negotiated_price_eur", sa.Numeric(14, 2)),
        sa.Column("deed_price_eur", sa.Numeric(14, 2)),
        sa.Column("observed_period", sa.Date(), nullable=False),
        sa.Column("market_data_consent", sa.Boolean(), nullable=False),
        sa.Column("privacy_notice_version", sa.String(30), nullable=False),
        sa.Column("status", sa.String(20), nullable=False, server_default="submitted"),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("expires_at", sa.DateTime(timezone=True), nullable=False),
        sa.CheckConstraint("surface_area_m2 > 0", name="ck_market_observation_surface_positive"),
        sa.CheckConstraint(
            "asking_price_eur IS NOT NULL OR appraisal_value_eur IS NOT NULL "
            "OR negotiated_price_eur IS NOT NULL OR deed_price_eur IS NOT NULL",
            name="ck_market_observation_has_price",
        ),
        schema="product",
    )
    op.create_index(
        "ix_product_market_observations_geo_period",
        "market_observations",
        ["geography_code", "observed_period"],
        schema="product",
    )
    op.create_index(
        "ix_product_market_observations_status_created",
        "market_observations",
        ["status", "created_at"],
        schema="product",
    )


def downgrade() -> None:
    op.drop_table("market_observations", schema="product")
