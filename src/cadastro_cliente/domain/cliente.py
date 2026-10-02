"""Entidade Cliente: só existe com todos os value objects válidos."""

from collections.abc import Mapping
from dataclasses import dataclass
from datetime import UTC, datetime
from uuid import UUID, uuid4

from cadastro_cliente.domain.contato import Email, Telefone
from cadastro_cliente.domain.documento import Documento, TipoPessoa
from cadastro_cliente.domain.endereco import Endereco
from cadastro_cliente.domain.erros import ColetorErros

_CAMPOS_ENDERECO = ("logradouro", "numero", "complemento", "bairro", "cidade", "uf", "cep")


def _validar(nome, documento, email, telefone, endereco):
    c = ColetorErros()
    end = endereco or {}
    validados = (
        c.texto(nome, "nome", 2, 150),
        c.tentar(Documento, documento),
        c.tentar(Email, email),
        c.tentar(Telefone, telefone),
        c.tentar(Endereco.criar, **{k: end.get(k) for k in _CAMPOS_ENDERECO}),
    )
    c.verificar()
    return validados


@dataclass(eq=False, repr=False)
class Cliente:
    id: UUID
    nome: str
    documento: Documento
    email: Email
    telefone: Telefone
    endereco: Endereco
    criado_em: datetime
    atualizado_em: datetime

    @property
    def tipo_pessoa(self) -> TipoPessoa:
        return self.documento.tipo

    @classmethod
    def criar(
        cls,
        *,
        nome: str | None,
        documento: str | None,
        email: str | None,
        telefone: str | None,
        endereco: Mapping[str, str | None] | None,
        agora: datetime | None = None,
    ) -> "Cliente":
        validados = _validar(nome, documento, email, telefone, endereco)
        momento = agora or datetime.now(UTC)
        return cls(uuid4(), *validados, criado_em=momento, atualizado_em=momento)

    def atualizar(
        self,
        *,
        nome: str | None,
        documento: str | None,
        email: str | None,
        telefone: str | None,
        endereco: Mapping[str, str | None] | None,
        agora: datetime | None = None,
    ) -> None:
        """Valida tudo antes de alterar: em caso de erro o cliente permanece intacto."""
        validados = _validar(nome, documento, email, telefone, endereco)
        self.nome, self.documento, self.email, self.telefone, self.endereco = validados
        self.atualizado_em = agora or datetime.now(UTC)

    def __eq__(self, outro: object) -> bool:
        return isinstance(outro, Cliente) and outro.id == self.id

    def __hash__(self) -> int:
        return hash(self.id)

    def __repr__(self) -> str:
        return f"Cliente(id={self.id}, tipo_pessoa={self.tipo_pessoa})"
