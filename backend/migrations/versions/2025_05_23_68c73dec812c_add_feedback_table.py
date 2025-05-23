"""add_feedback_table

Revision ID: 68c73dec812c
Revises: a41f229f5c91
Create Date: 2025-05-23 12:18:37.725754

"""

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

# revision identifiers, used by Alembic.
revision: str = "68c73dec812c"
down_revision: Union[str, None] = "a41f229f5c91"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "feedback",
        sa.Column("feedback_id", sa.Integer(), nullable=False),
        sa.Column("user_id", sa.Integer(), nullable=False),
        sa.Column("feedback_type", sa.String(), nullable=False),
        sa.Column("comment", sa.Text(), nullable=True),
        sa.Column("search_term", sa.Text(), nullable=False),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.text("now()"),
        ),
        sa.ForeignKeyConstraint(
            ["user_id"],
            ["users.user_id"],
        ),
        sa.PrimaryKeyConstraint("feedback_id"),
    )
    op.create_index(
        op.f("ix_feedback_feedback_id"), "feedback", ["feedback_id"], unique=False
    )


def downgrade() -> None:
    op.drop_index(op.f("ix_feedback_feedback_id"), table_name="feedback")
    op.drop_table("feedback")
