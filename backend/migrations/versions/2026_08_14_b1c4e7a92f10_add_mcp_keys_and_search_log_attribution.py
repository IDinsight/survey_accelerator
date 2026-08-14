"""Add MCP personal keys and widen search log attribution

Lets searches arrive from the MCP server as well as the web app. The log's
user_id becomes nullable because MCP callers may be anonymous, and source plus
client_ip record where a search came from -- client_ip is what the anonymous
rate limit counts against.

Revision ID: b1c4e7a92f10
Revises: 68c73dec812c
Create Date: 2026-08-14

"""

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

# revision identifiers, used by Alembic.
revision: str = "b1c4e7a92f10"
down_revision: Union[str, None] = "68c73dec812c"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Add the key column and the log attribution columns."""
    op.add_column(
        "users", sa.Column("mcp_key_hash", sa.String(length=64), nullable=True)
    )
    op.create_index("ix_users_mcp_key_hash", "users", ["mcp_key_hash"], unique=True)

    op.alter_column("search_logs", "user_id", existing_type=sa.Integer(), nullable=True)
    op.add_column(
        "search_logs", sa.Column("source", sa.String(length=20), nullable=True)
    )
    op.add_column(
        "search_logs", sa.Column("client_ip", sa.String(length=64), nullable=True)
    )
    op.create_index(
        "ix_search_logs_source_ip_time",
        "search_logs",
        ["source", "client_ip", "timestamp"],
    )
    # Everything logged before this point came from the web app.
    op.execute("UPDATE search_logs SET source = 'web' WHERE source IS NULL")


def downgrade() -> None:
    """Drop the added columns and restore the NOT NULL constraint."""
    op.drop_index("ix_search_logs_source_ip_time", table_name="search_logs")
    op.drop_column("search_logs", "client_ip")
    op.drop_column("search_logs", "source")
    # Rows without a user cannot satisfy the restored constraint.
    op.execute("DELETE FROM search_logs WHERE user_id IS NULL")
    op.alter_column(
        "search_logs", "user_id", existing_type=sa.Integer(), nullable=False
    )

    op.drop_index("ix_users_mcp_key_hash", table_name="users")
    op.drop_column("users", "mcp_key_hash")
