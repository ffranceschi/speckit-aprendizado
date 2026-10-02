"""criar tabela clientes

Revision ID: 0001
Revises:
Create Date: 2026-10-02
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "0001"
down_revision: str | None = None
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_table(
        "clientes",
        sa.Column("id", sa.Uuid(), primary_key=True),
        sa.Column("nome", sa.String(150), nullable=False),
        sa.Column("tipo_pessoa", sa.String(8), nullable=False),
        sa.Column("documento_hash", sa.LargeBinary(32), nullable=False),
        sa.Column("documento_cifrado", sa.LargeBinary(), nullable=False),
        sa.Column("email_cifrado", sa.LargeBinary(), nullable=False),
        sa.Column("telefone_cifrado", sa.LargeBinary(), nullable=False),
        sa.Column("endereco_cifrado", sa.LargeBinary(), nullable=False),
        sa.Column("criado_em", sa.DateTime(timezone=True), nullable=False),
        sa.Column("atualizado_em", sa.DateTime(timezone=True), nullable=False),
        sa.UniqueConstraint("documento_hash", name="uq_clientes_documento_hash"),
        sa.CheckConstraint("tipo_pessoa IN ('FISICA', 'JURIDICA')", name="ck_clientes_tipo_pessoa"),
    )
    op.create_index("ix_clientes_nome", "clientes", ["nome", "id"])


def downgrade() -> None:
    op.drop_index("ix_clientes_nome", table_name="clientes")
    op.drop_table("clientes")
