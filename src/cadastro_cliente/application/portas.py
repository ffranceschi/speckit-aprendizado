"""Portas (interfaces) que a camada de aplicação exige da infraestrutura."""

import math
from dataclasses import dataclass
from typing import Protocol
from uuid import UUID

from cadastro_cliente.domain.cliente import Cliente
from cadastro_cliente.domain.documento import Documento


@dataclass(frozen=True)
class Pagina[T]:
    itens: list[T]
    pagina: int
    tamanho: int
    total_itens: int

    @property
    def total_paginas(self) -> int:
        return math.ceil(self.total_itens / self.tamanho)


class ClienteRepository(Protocol):
    def adicionar(self, cliente: Cliente) -> None:
        """Lança DocumentoDuplicadoError se o documento já existir."""

    def atualizar(self, cliente: Cliente) -> None:
        """Lança DocumentoDuplicadoError se o documento pertencer a outro cliente."""

    def obter(self, id_: UUID) -> Cliente | None: ...

    def remover(self, id_: UUID) -> bool:
        """Exclusão definitiva. Retorna False se o cliente não existir."""

    def existe_documento(self, documento: Documento, ignorar_id: UUID | None = None) -> bool: ...

    def listar(self, pagina: int, tamanho: int) -> Pagina[Cliente]:
        """Ordenado por nome e id."""


class ProtetorDados(Protocol):
    def cifrar(self, valor: str) -> bytes: ...

    def decifrar(self, dados: bytes) -> str: ...

    def hash_documento(self, documento: str) -> bytes: ...
