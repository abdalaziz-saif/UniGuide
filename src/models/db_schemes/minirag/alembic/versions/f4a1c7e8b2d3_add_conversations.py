"""Add conversation memory tables.

Revision ID: f4a1c7e8b2d3
Revises: d3008295d1e4
Create Date: 2026-09-23 00:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql


revision: str = "f4a1c7e8b2d3"
down_revision: Union[str, Sequence[str], None] = "d3008295d1e4"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "conversations",
        sa.Column("conversation_id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("conversation_uuid", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("conversation_project_id", sa.Integer(), nullable=False),
        sa.Column("title", sa.String(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=True),
        sa.ForeignKeyConstraint(["conversation_project_id"], ["projects.project_id"]),
        sa.PrimaryKeyConstraint("conversation_id"),
        sa.UniqueConstraint("conversation_uuid"),
    )
    op.create_index(
        "ix_conversation_project_id",
        "conversations",
        ["conversation_project_id"],
        unique=False,
    )

    op.create_table(
        "messages",
        sa.Column("message_id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("message_conversation_id", sa.Integer(), nullable=False),
        sa.Column("role", sa.String(), nullable=False),
        sa.Column("content", sa.Text(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.ForeignKeyConstraint(["message_conversation_id"], ["conversations.conversation_id"]),
        sa.PrimaryKeyConstraint("message_id"),
    )
    op.create_index(
        "ix_message_conversation_id",
        "messages",
        ["message_conversation_id"],
        unique=False,
    )


def downgrade() -> None:
    op.drop_index("ix_message_conversation_id", table_name="messages")
    op.drop_table("messages")
    op.drop_index("ix_conversation_project_id", table_name="conversations")
    op.drop_table("conversations")