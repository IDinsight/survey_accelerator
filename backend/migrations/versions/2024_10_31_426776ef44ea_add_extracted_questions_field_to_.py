"""Add extracted questions field to DocumentDB

Revision ID: 426776ef44ea
Revises: 2f85a60d67ab
Create Date: 2024-10-31 17:43:27.068778

"""

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

# revision identifiers, used by Alembic.
revision: str = "426776ef44ea"
down_revision: Union[str, None] = "2f85a60d67ab"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # ### commands auto generated by Alembic - please adjust! ###
    op.add_column(
        "documents", sa.Column("extracted_question_answers", sa.Text(), nullable=True)
    )
    # ### end Alembic commands ###


def downgrade() -> None:
    # ### commands auto generated by Alembic - please adjust! ###
    op.drop_column("documents", "extracted_question_answers")
    # ### end Alembic commands ###