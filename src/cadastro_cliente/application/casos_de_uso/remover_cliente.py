import logging
from uuid import UUID

from cadastro_cliente.application.portas import ClienteRepository
from cadastro_cliente.domain.erros import ClienteNaoEncontradoError

logger = logging.getLogger(__name__)


class RemoverCliente:
    """Exclusão definitiva (FR-016): os dados pessoais não são retidos."""

    def __init__(self, repositorio: ClienteRepository):
        self._repositorio = repositorio

    def executar(self, id_: UUID) -> None:
        if not self._repositorio.remover(id_):
            raise ClienteNaoEncontradoError()
        logger.info("cliente_removido", extra={"cliente_id": str(id_)})
