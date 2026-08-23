"""initial schema

Revision ID: 0001
Revises:
Create Date: 2026-08-23

"""
from collections.abc import Sequence

import sqlalchemy as sa
from pgvector.sqlalchemy import Vector

from alembic import op

revision: str = "0001"
down_revision: str | None = None
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.execute("CREATE EXTENSION IF NOT EXISTS vector")

    op.create_table(
        "categoria",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("nome", sa.String(length=100), nullable=False),
        sa.Column("slug", sa.String(length=100), nullable=False, unique=True),
    )

    op.create_table(
        "faq_item",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("categoria_id", sa.Integer(), sa.ForeignKey("categoria.id"), nullable=False),
        sa.Column("pergunta", sa.Text(), nullable=False),
        sa.Column("resposta", sa.Text(), nullable=False),
        sa.Column("ativo", sa.Boolean(), nullable=False, server_default=sa.true()),
        sa.Column("embedding", Vector(1536), nullable=True),
        sa.Column("criado_em", sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.Column("atualizado_em", sa.DateTime(timezone=True), server_default=sa.func.now()),
    )

    op.create_table(
        "interacao",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("pergunta_usuario", sa.Text(), nullable=False),
        sa.Column(
            "faq_item_id", sa.Integer(), sa.ForeignKey("faq_item.id", ondelete="SET NULL"), nullable=True
        ),
        sa.Column(
            "categoria_id", sa.Integer(), sa.ForeignKey("categoria.id", ondelete="SET NULL"), nullable=True
        ),
        sa.Column("score_similaridade", sa.Float(), nullable=True),
        sa.Column("sem_resposta", sa.Boolean(), nullable=False, server_default=sa.false()),
        sa.Column("embedding", Vector(1536), nullable=True),
        sa.Column("criado_em", sa.DateTime(timezone=True), server_default=sa.func.now()),
    )
    op.create_index("ix_interacao_criado_em", "interacao", ["criado_em"])
    op.create_index("ix_interacao_sem_resposta", "interacao", ["sem_resposta"])


def downgrade() -> None:
    op.drop_index("ix_interacao_sem_resposta", table_name="interacao")
    op.drop_index("ix_interacao_criado_em", table_name="interacao")
    op.drop_table("interacao")
    op.drop_table("faq_item")
    op.drop_table("categoria")
