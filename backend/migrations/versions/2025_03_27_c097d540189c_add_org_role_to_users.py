"""Add org + role to users

Revision ID: c097d540189c
Revises: 576c81bdf98f
Create Date: 2025-03-27 18:05:03.088153

"""

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

# revision identifiers, used by Alembic.
revision: str = "c097d540189c"
down_revision: Union[str, None] = "576c81bdf98f"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # ### commands auto generated by Alembic - please adjust! ###
    op.add_column("users", sa.Column("organization", sa.String(), nullable=False))
    op.add_column("users", sa.Column("role", sa.String(), nullable=False))
    # ### end Alembic commands ###


def downgrade() -> None:
    # ### commands auto generated by Alembic - please adjust! ###
    op.drop_column("users", "role")
    op.drop_column("users", "organization")
    # ### end Alembic commands ###
