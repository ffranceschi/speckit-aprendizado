"""Schemas HTTP (contracts/openapi.yaml). Validam apenas forma/tipos; regras ficam no domínio (R3).

Os campos de entrada aceitam ausência (None) para que o domínio reporte TODOS os campos
obrigatórios faltantes de uma vez (FR-010).
"""

from datetime import datetime
from typing import Literal
from uuid import UUID

from pydantic import BaseModel, ConfigDict

from cadastro_cliente.application.dto import DadosCliente, DadosEndereco
from cadastro_cliente.application.portas import Pagina
from cadastro_cliente.domain.cliente import Cliente


class EnderecoEntrada(BaseModel):
    model_config = ConfigDict(hide_input_in_errors=True)

    logradouro: str | None = None
    numero: str | None = None
    complemento: str | None = None
    bairro: str | None = None
    cidade: str | None = None
    uf: str | None = None
    cep: str | None = None


class ClienteEntrada(BaseModel):
    model_config = ConfigDict(hide_input_in_errors=True)

    nome: str | None = None
    documento: str | None = None
    email: str | None = None
    telefone: str | None = None
    endereco: EnderecoEntrada | None = None

    def para_dados(self) -> DadosCliente:
        return DadosCliente(
            nome=self.nome,
            documento=self.documento,
            email=self.email,
            telefone=self.telefone,
            endereco=DadosEndereco(**self.endereco.model_dump()) if self.endereco else None,
        )


class Endereco(BaseModel):
    logradouro: str
    numero: str
    complemento: str | None
    bairro: str
    cidade: str
    uf: str
    cep: str


class ClienteDetalhe(BaseModel):
    id: UUID
    nome: str
    documento: str
    tipo_pessoa: Literal["FISICA", "JURIDICA"]
    email: str
    telefone: str
    endereco: Endereco
    criado_em: datetime
    atualizado_em: datetime

    @classmethod
    def de_cliente(cls, cliente: Cliente) -> "ClienteDetalhe":
        end = cliente.endereco
        return cls(
            id=cliente.id,
            nome=cliente.nome,
            documento=cliente.documento.formatado(),
            tipo_pessoa=cliente.tipo_pessoa.value,
            email=cliente.email.valor,
            telefone=cliente.telefone.formatado(),
            endereco=Endereco(**{**end.para_dict(), "cep": end.cep_formatado()}),
            criado_em=cliente.criado_em,
            atualizado_em=cliente.atualizado_em,
        )


class ClienteResumo(BaseModel):
    id: UUID
    nome: str
    documento_mascarado: str
    tipo_pessoa: Literal["FISICA", "JURIDICA"]
    email: str
    telefone: str

    @classmethod
    def de_cliente(cls, cliente: Cliente) -> "ClienteResumo":
        return cls(
            id=cliente.id,
            nome=cliente.nome,
            documento_mascarado=cliente.documento.mascarado(),
            tipo_pessoa=cliente.tipo_pessoa.value,
            email=cliente.email.valor,
            telefone=cliente.telefone.formatado(),
        )


class PaginaClientes(BaseModel):
    items: list[ClienteResumo]
    page: int
    page_size: int
    total_items: int
    total_pages: int

    @classmethod
    def de_pagina(cls, pagina: Pagina[Cliente]) -> "PaginaClientes":
        return cls(
            items=[ClienteResumo.de_cliente(c) for c in pagina.itens],
            page=pagina.pagina,
            page_size=pagina.tamanho,
            total_items=pagina.total_itens,
            total_pages=pagina.total_paginas,
        )


class ErroCampo(BaseModel):
    field: str | None
    code: str
    message: str


class Erros(BaseModel):
    errors: list[ErroCampo]
