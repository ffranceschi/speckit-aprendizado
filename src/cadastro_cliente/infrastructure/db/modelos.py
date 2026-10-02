"""Modelo de persistência do Cliente (data-model.md, tabela `clientes`)."""

from datetime import datetime
from uuid import UUID

from sqlalchemy import CheckConstraint, DateTime, Index, LargeBinary, String, UniqueConstraint
from sqlalchemy import Uuid as SAUuid
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column


class Base(DeclarativeBase):
    pass


class ClienteModel(Base):
    __tablename__ = "clientes"
    __table_args__ = (
        UniqueConstraint("documento_hash", name="uq_clientes_documento_hash"),
        CheckConstraint("tipo_pessoa IN ('FISICA', 'JURIDICA')", name="ck_clientes_tipo_pessoa"),
        Index("ix_clientes_nome", "nome", "id"),
    )

    id: Mapped[UUID] = mapped_column(SAUuid, primary_key=True)
    nome: Mapped[str] = mapped_column(String(150), nullable=False)
    tipo_pessoa: Mapped[str] = mapped_column(String(8), nullable=False)
    documento_hash: Mapped[bytes] = mapped_column(LargeBinary(32), nullable=False)
    documento_cifrado: Mapped[bytes] = mapped_column(LargeBinary, nullable=False)
    email_cifrado: Mapped[bytes] = mapped_column(LargeBinary, nullable=False)
    telefone_cifrado: Mapped[bytes] = mapped_column(LargeBinary, nullable=False)
    endereco_cifrado: Mapped[bytes] = mapped_column(LargeBinary, nullable=False)
    criado_em: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    atualizado_em: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)

    def __repr__(self) -> str:
        return f"ClienteModel(id={self.id})"
