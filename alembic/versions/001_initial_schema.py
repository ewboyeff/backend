"""Initial schema."""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql


# revision identifiers, used by Alembic.
revision: str = "001_initial_schema"
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def _base_columns() -> list[sa.Column]:
    return [
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
    ]


def upgrade() -> None:
    bind = op.get_bind()

    # Create enums explicitly first (checkfirst=True = idempotent)
    for name, values in [
        ("fund_status", ["active", "inactive", "suspended"]),
        ("index_grade", ["platinum", "gold", "silver", "bronze", "unrated"]),
        ("index_type", ["transparency", "openness", "trust"]),
        ("project_status", ["planned", "active", "completed"]),
        ("report_type", ["annual", "quarterly", "monthly"]),
        ("user_role", ["user", "fund_rep", "moderator", "admin"]),
        ("complaint_status", ["pending", "reviewed", "resolved"]),
    ]:
        postgresql.ENUM(*values, name=name).create(bind, checkfirst=True)

    # create_type=False: don't auto-create enums on table creation (already done above)
    fund_status_enum = postgresql.ENUM("active", "inactive", "suspended", name="fund_status", create_type=False)
    index_grade_enum = postgresql.ENUM("platinum", "gold", "silver", "bronze", "unrated", name="index_grade", create_type=False)
    index_type_enum = postgresql.ENUM("transparency", "openness", "trust", name="index_type", create_type=False)
    project_status_enum = postgresql.ENUM("planned", "active", "completed", name="project_status", create_type=False)
    report_type_enum = postgresql.ENUM("annual", "quarterly", "monthly", name="report_type", create_type=False)
    user_role_enum = postgresql.ENUM("user", "fund_rep", "moderator", "admin", name="user_role", create_type=False)
    complaint_status_enum = postgresql.ENUM("pending", "reviewed", "resolved", name="complaint_status", create_type=False)

    op.create_table(
        "categories",
        *_base_columns(),
        sa.Column("name_uz", sa.String(length=255), nullable=False),
        sa.Column("name_ru", sa.String(length=255), nullable=True),
        sa.Column("name_en", sa.String(length=255), nullable=True),
        sa.Column("slug", sa.String(length=255), nullable=False),
        sa.Column("icon_url", sa.String(length=500), nullable=True),
        sa.Column("is_active", sa.Boolean(), server_default=sa.text("true"), nullable=False),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("slug", name="uq_categories_slug"),
    )

    op.create_table(
        "regions",
        *_base_columns(),
        sa.Column("name_uz", sa.String(length=255), nullable=False),
        sa.Column("name_ru", sa.String(length=255), nullable=True),
        sa.Column("name_en", sa.String(length=255), nullable=True),
        sa.Column("code", sa.String(length=10), nullable=False),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("code", name="uq_regions_code"),
    )

    op.create_table(
        "funds",
        *_base_columns(),
        sa.Column("name_uz", sa.String(length=255), nullable=False),
        sa.Column("name_ru", sa.String(length=255), nullable=True),
        sa.Column("name_en", sa.String(length=255), nullable=True),
        sa.Column("slug", sa.String(length=255), nullable=False),
        sa.Column("description_uz", sa.Text(), nullable=True),
        sa.Column("description_ru", sa.Text(), nullable=True),
        sa.Column("description_en", sa.Text(), nullable=True),
        sa.Column("logo_url", sa.String(length=500), nullable=True),
        sa.Column("logo_initials", sa.String(length=10), nullable=True),
        sa.Column("logo_color", sa.String(length=20), nullable=True),
        sa.Column("director_name", sa.String(length=255), nullable=True),
        sa.Column("founded_year", sa.Integer(), nullable=True),
        sa.Column("legal_address", sa.Text(), nullable=True),
        sa.Column("inn", sa.String(length=20), nullable=True),
        sa.Column("registration_number", sa.String(length=100), nullable=True),
        sa.Column("category_id", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("region_id", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("website_url", sa.String(length=500), nullable=True),
        sa.Column("telegram_url", sa.String(length=500), nullable=True),
        sa.Column("instagram_url", sa.String(length=500), nullable=True),
        sa.Column("is_verified", sa.Boolean(), server_default=sa.text("false"), nullable=False),
        sa.Column("is_active", sa.Boolean(), server_default=sa.text("true"), nullable=False),
        sa.Column("status", fund_status_enum, server_default="active", nullable=False),
        sa.ForeignKeyConstraint(["category_id"], ["categories.id"], ondelete="SET NULL"),
        sa.ForeignKeyConstraint(["region_id"], ["regions.id"], ondelete="SET NULL"),
        sa.PrimaryKeyConstraint("id"),
    )

    op.create_table(
        "index_factors",
        *_base_columns(),
        sa.Column("index_type", index_type_enum, nullable=False),
        sa.Column("name_uz", sa.String(length=255), nullable=False),
        sa.Column("name_ru", sa.String(length=255), nullable=True),
        sa.Column("name_en", sa.String(length=255), nullable=True),
        sa.Column("weight", sa.Numeric(5, 2), nullable=False),
        sa.Column("is_active", sa.Boolean(), server_default=sa.text("true"), nullable=False),
        sa.Column("order", sa.Integer(), server_default=sa.text("0"), nullable=False),
        sa.PrimaryKeyConstraint("id"),
    )

    op.create_table(
        "fund_indexes",
        *_base_columns(),
        sa.Column("fund_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("transparency_score", sa.Numeric(5, 2), server_default=sa.text("0"), nullable=False),
        sa.Column("openness_score", sa.Numeric(5, 2), server_default=sa.text("0"), nullable=False),
        sa.Column("trust_score", sa.Numeric(5, 2), server_default=sa.text("0"), nullable=False),
        sa.Column("overall_score", sa.Numeric(5, 2), server_default=sa.text("0"), nullable=False),
        sa.Column("grade", index_grade_enum, server_default="unrated", nullable=False),
        sa.Column("calculated_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("valid_until", sa.DateTime(timezone=True), nullable=True),
        sa.ForeignKeyConstraint(["fund_id"], ["funds.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )

    op.create_table(
        "fund_index_scores",
        *_base_columns(),
        sa.Column("fund_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("factor_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("score", sa.Numeric(5, 2), server_default=sa.text("0"), nullable=False),
        sa.Column("note", sa.Text(), nullable=True),
        sa.Column("calculated_at", sa.DateTime(timezone=True), nullable=True),
        sa.ForeignKeyConstraint(["factor_id"], ["index_factors.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["fund_id"], ["funds.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("fund_id", "factor_id", name="uq_fund_index_scores_fund_factor"),
    )

    op.create_table(
        "projects",
        *_base_columns(),
        sa.Column("fund_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("title_uz", sa.String(length=255), nullable=False),
        sa.Column("title_ru", sa.String(length=255), nullable=True),
        sa.Column("title_en", sa.String(length=255), nullable=True),
        sa.Column("description_uz", sa.Text(), nullable=True),
        sa.Column("description_ru", sa.Text(), nullable=True),
        sa.Column("description_en", sa.Text(), nullable=True),
        sa.Column("status", project_status_enum, server_default="planned", nullable=False),
        sa.Column("budget", sa.Numeric(15, 2), server_default=sa.text("0"), nullable=False),
        sa.Column("spent", sa.Numeric(15, 2), server_default=sa.text("0"), nullable=False),
        sa.Column("currency", sa.String(length=10), server_default="UZS", nullable=False),
        sa.Column("beneficiaries_count", sa.Integer(), server_default=sa.text("0"), nullable=False),
        sa.Column("start_date", sa.Date(), nullable=True),
        sa.Column("end_date", sa.Date(), nullable=True),
        sa.Column("region_id", postgresql.UUID(as_uuid=True), nullable=True),
        sa.ForeignKeyConstraint(["fund_id"], ["funds.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["region_id"], ["regions.id"], ondelete="SET NULL"),
        sa.PrimaryKeyConstraint("id"),
    )

    op.create_table(
        "financial_reports",
        *_base_columns(),
        sa.Column("fund_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("report_type", report_type_enum, nullable=False),
        sa.Column("period_start", sa.Date(), nullable=True),
        sa.Column("period_end", sa.Date(), nullable=True),
        sa.Column("total_income", sa.Numeric(15, 2), server_default=sa.text("0"), nullable=False),
        sa.Column("total_expense", sa.Numeric(15, 2), server_default=sa.text("0"), nullable=False),
        sa.Column("file_url", sa.String(length=500), nullable=True),
        sa.Column("is_verified", sa.Boolean(), server_default=sa.text("false"), nullable=False),
        sa.ForeignKeyConstraint(["fund_id"], ["funds.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )

    op.create_table(
        "users",
        *_base_columns(),
        sa.Column("email", sa.String(length=255), nullable=False),
        sa.Column("password_hash", sa.String(length=500), nullable=False),
        sa.Column("full_name", sa.String(length=255), nullable=True),
        sa.Column("role", user_role_enum, server_default="user", nullable=False),
        sa.Column("is_active", sa.Boolean(), server_default=sa.text("true"), nullable=False),
        sa.Column("fund_id", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("preferred_language", sa.String(length=5), server_default="uz", nullable=False),
        sa.Column("last_login", sa.DateTime(timezone=True), nullable=True),
        sa.ForeignKeyConstraint(["fund_id"], ["funds.id"], ondelete="SET NULL"),
        sa.PrimaryKeyConstraint("id"),
    )

    op.create_table(
        "reviews",
        *_base_columns(),
        sa.Column("fund_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("user_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("rating", sa.Integer(), nullable=False),
        sa.Column("comment", sa.Text(), nullable=True),
        sa.Column("is_approved", sa.Boolean(), server_default=sa.text("false"), nullable=False),
        sa.CheckConstraint("rating >= 1 AND rating <= 5", name="ck_reviews_rating_range"),
        sa.ForeignKeyConstraint(["fund_id"], ["funds.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("fund_id", "user_id", name="uq_reviews_fund_user"),
    )

    op.create_table(
        "complaints",
        *_base_columns(),
        sa.Column("fund_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("user_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("reason", sa.String(length=255), nullable=False),
        sa.Column("description", sa.Text(), nullable=True),
        sa.Column("status", complaint_status_enum, server_default="pending", nullable=False),
        sa.Column("admin_note", sa.Text(), nullable=True),
        sa.ForeignKeyConstraint(["fund_id"], ["funds.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )

    op.create_table(
        "news",
        *_base_columns(),
        sa.Column("fund_id", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("title_uz", sa.String(length=255), nullable=False),
        sa.Column("title_ru", sa.String(length=255), nullable=True),
        sa.Column("title_en", sa.String(length=255), nullable=True),
        sa.Column("content_uz", sa.Text(), nullable=True),
        sa.Column("content_ru", sa.Text(), nullable=True),
        sa.Column("content_en", sa.Text(), nullable=True),
        sa.Column("image_url", sa.String(length=500), nullable=True),
        sa.Column("source_url", sa.String(length=500), nullable=True),
        sa.Column("gradient", sa.String(length=100), nullable=True),
        sa.Column("read_time", sa.Integer(), server_default=sa.text("3"), nullable=False),
        sa.Column("is_featured", sa.Boolean(), server_default=sa.text("false"), nullable=False),
        sa.Column("is_active", sa.Boolean(), server_default=sa.text("true"), nullable=False),
        sa.Column("published_at", sa.DateTime(timezone=True), nullable=True),
        sa.ForeignKeyConstraint(["fund_id"], ["funds.id"], ondelete="SET NULL"),
        sa.PrimaryKeyConstraint("id"),
    )

    op.create_index("ix_funds_slug", "funds", ["slug"], unique=True)
    op.create_index("ix_users_email", "users", ["email"], unique=True)
    op.create_index("ix_fund_indexes_fund_id", "fund_indexes", ["fund_id"], unique=True)
    op.create_index(
        "ix_fund_index_scores_fund_id_factor_id",
        "fund_index_scores",
        ["fund_id", "factor_id"],
        unique=False,
    )


def downgrade() -> None:
    op.drop_index("ix_fund_index_scores_fund_id_factor_id", table_name="fund_index_scores")
    op.drop_index("ix_fund_indexes_fund_id", table_name="fund_indexes")
    op.drop_index("ix_users_email", table_name="users")
    op.drop_index("ix_funds_slug", table_name="funds")

    op.drop_table("news")
    op.drop_table("complaints")
    op.drop_table("reviews")
    op.drop_table("users")
    op.drop_table("financial_reports")
    op.drop_table("projects")
    op.drop_table("fund_index_scores")
    op.drop_table("fund_indexes")
    op.drop_table("index_factors")
    op.drop_table("funds")
    op.drop_table("regions")
    op.drop_table("categories")

    op.execute("DROP TYPE IF EXISTS complaint_status")
    op.execute("DROP TYPE IF EXISTS user_role")
    op.execute("DROP TYPE IF EXISTS report_type")
    op.execute("DROP TYPE IF EXISTS project_status")
    op.execute("DROP TYPE IF EXISTS index_type")
    op.execute("DROP TYPE IF EXISTS index_grade")
    op.execute("DROP TYPE IF EXISTS fund_status")
