from cadastro_cliente.application.dto import TAMANHO_PAGINA
from cadastro_cliente.application.portas import ClienteRepository, Pagina
from cadastro_cliente.domain.cliente import Cliente
from cadastro_cliente.domain.erros import DadosInvalidosError, ErroCampo


class ListarClientes:
    def __init__(self, repositorio: ClienteRepository):
        self._repositorio = repositorio

    def executar(self, pagina: int = 1) -> Pagina[Cliente]:
        if pagina < 1:
            raise DadosInvalidosError(
                [ErroCampo("page", "pagina_invalida", "A página deve ser maior ou igual a 1.")]
            )
        return self._repositorio.listar(pagina, TAMANHO_PAGINA)
