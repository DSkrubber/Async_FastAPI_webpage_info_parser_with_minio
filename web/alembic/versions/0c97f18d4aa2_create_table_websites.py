"""create table websites

Revision ID: 0c97f18d4aa2
Revises:
Create Date: 2022-05-11 22:25:05.522474

"""
from enum import Enum

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = "0c97f18d4aa2"
down_revision = None
branch_labels = None
depends_on = None


class ParsingStatus(str, Enum):
    pending = "pending"
    in_progress = "in_progress"
    failed = "failed"
    finished = "finished"


def upgrade():
    op.create_table(
        "websites",
        sa.Column("website_id", sa.INTEGER(), nullable=False),
        sa.Column("url", sa.VARCHAR(), nullable=False),
        sa.Column("html_length", sa.INTEGER(), nullable=True),
        sa.Column(
            "pictures_keys",
            postgresql.ARRAY(sa.VARCHAR()),
            server_default="{}",
            nullable=False,
        ),
        sa.Column(
            "created_at",
            sa.TIMESTAMP(),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.PrimaryKeyConstraint("website_id"),
        sa.UniqueConstraint("url"),
    )
    parsing_status = postgresql.ENUM(ParsingStatus, name="parsingstatus")
    parsing_status.create(op.get_bind(), checkfirst=True)
    op.add_column(
        "websites", sa.Column("parsing_status", parsing_status, nullable=False)
    )
    op.create_index(
        op.f("ix_websites_created_at"),
        "websites",
        ["created_at"],
        unique=False,
    )


def downgrade():
    op.drop_index(op.f("ix_websites_created_at"), table_name="websites")
    op.drop_table("websites")
    op.execute("DROP TYPE parsingstatus;")
