"""remove_qa_pairs_table

Revision ID: 35ee0d11e037
Revises: 62342bab6861
Create Date: 2025-03-07 16:58:38.365412

"""

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

# revision identifiers, used by Alembic.
revision: str = "35ee0d11e037"
down_revision: Union[str, None] = "62342bab6861"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Drop the qa_pairs table
    op.drop_table("qa_pairs")

    # Drop the precision column from search_logs
    with op.batch_alter_table("search_logs") as batch_op:
        batch_op.drop_column("precision")


def downgrade() -> None:
    # Recreate the qa_pairs table
    op.create_table(
        "qa_pairs",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("document_id", sa.Integer(), nullable=False),
        sa.Column("question", sa.Text(), nullable=False),
        sa.Column("answer", sa.Text(), nullable=False),
        sa.ForeignKeyConstraint(["document_id"], ["documents.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )

    # Add the precision column back to search_logs
    with op.batch_alter_table("search_logs") as batch_op:
        batch_op.add_column(
            sa.Column("precision", sa.Boolean(), nullable=False, server_default="false")
        )
