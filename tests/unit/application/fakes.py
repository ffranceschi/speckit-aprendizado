"""Dublês das portas para testar casos de uso sem banco (Princípio II)."""

import copy
from uuid import UUID

from cadastro_cliente.application.portas import Pagina
from cadastro_cliente.domain.cliente import Cliente
from cadastro_cliente.domain.documento import Documento
from cadastro_cliente.domain.erros import DocumentoDuplicadoError


class RepositorioClienteEmMemoria:
    def __init__(self, clientes: list[Cliente] | None = None):
        self._dados: dict[UUID, Cliente] = {}
        for cliente in clientes or []:
            self.adicionar(cliente)

    def _conflito(self, cliente: Cliente) -> bool:
        return any(
            c.documento == cliente.documento and c.id != cliente.id for c in self._dados.values()
        )

    def adicionar(self, cliente: Cliente) -> None:
        if self._conflito(cliente):
            raise DocumentoDuplicadoError()
        self._dados[cliente.id] = copy.deepcopy(cliente)

    def atualizar(self, cliente: Cliente) -> None:
        if self._conflito(cliente):
            raise DocumentoDuplicadoError()
        self._dados[cliente.id] = copy.deepcopy(cliente)

    def obter(self, id_: UUID) -> Cliente | None:
        cliente = self._dados.get(id_)
        return copy.deepcopy(cliente) if cliente else None

    def remover(self, id_: UUID) -> bool:
        return self._dados.pop(id_, None) is not None

    def existe_documento(self, documento: Documento, ignorar_id: UUID | None = None) -> bool:
        return any(c.documento == documento and c.id != ignorar_id for c in self._dados.values())

    def listar(self, pagina: int, tamanho: int) -> Pagina[Cliente]:
        ordenados = sorted(self._dados.values(), key=lambda c: (c.nome, str(c.id)))
        inicio = (pagina - 1) * tamanho
        return Pagina(
            itens=[copy.deepcopy(c) for c in ordenados[inicio : inicio + tamanho]],
            pagina=pagina,
            tamanho=tamanho,
            total_itens=len(ordenados),
        )

    def __len__(self) -> int:
        return len(self._dados)
