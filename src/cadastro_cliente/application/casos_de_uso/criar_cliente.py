import logging

from cadastro_cliente.application.dto import DadosCliente
from cadastro_cliente.application.portas import ClienteRepository
from cadastro_cliente.domain.cliente import Cliente
from cadastro_cliente.domain.erros import DocumentoDuplicadoError

logger = logging.getLogger(__name__)


class CriarCliente:
    def __init__(self, repositorio: ClienteRepository):
        self._repositorio = repositorio

    def executar(self, dados: DadosCliente) -> Cliente:
        cliente = Cliente.criar(**dados.como_kwargs())
        if self._repositorio.existe_documento(cliente.documento):
            raise DocumentoDuplicadoError()
        self._repositorio.adicionar(cliente)
        # Apenas identificadores: nunca dados pessoais (Princípio IV).
        logger.info(
            "cliente_criado",
            extra={"cliente_id": str(cliente.id), "tipo_pessoa": cliente.tipo_pessoa.value},
        )
        return cliente
