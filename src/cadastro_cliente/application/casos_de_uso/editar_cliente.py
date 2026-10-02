import logging
from uuid import UUID

from cadastro_cliente.application.dto import DadosCliente
from cadastro_cliente.application.portas import ClienteRepository
from cadastro_cliente.domain.cliente import Cliente
from cadastro_cliente.domain.erros import ClienteNaoEncontradoError, DocumentoDuplicadoError

logger = logging.getLogger(__name__)


class EditarCliente:
    def __init__(self, repositorio: ClienteRepository):
        self._repositorio = repositorio

    def executar(self, id_: UUID, dados: DadosCliente) -> Cliente:
        cliente = self._repositorio.obter(id_)
        if cliente is None:
            raise ClienteNaoEncontradoError()
        cliente.atualizar(**dados.como_kwargs())
        if self._repositorio.existe_documento(cliente.documento, ignorar_id=cliente.id):
            raise DocumentoDuplicadoError()
        self._repositorio.atualizar(cliente)
        logger.info("cliente_atualizado", extra={"cliente_id": str(cliente.id)})
        return cliente
