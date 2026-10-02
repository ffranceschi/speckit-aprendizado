from uuid import UUID

from cadastro_cliente.application.portas import ClienteRepository
from cadastro_cliente.domain.cliente import Cliente
from cadastro_cliente.domain.erros import ClienteNaoEncontradoError


class ObterCliente:
    def __init__(self, repositorio: ClienteRepository):
        self._repositorio = repositorio

    def executar(self, id_: UUID) -> Cliente:
        cliente = self._repositorio.obter(id_)
        if cliente is None:
            raise ClienteNaoEncontradoError()
        return cliente
