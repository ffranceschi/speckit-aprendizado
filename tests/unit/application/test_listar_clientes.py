import pytest

from cadastro_cliente.application.casos_de_uso.listar_clientes import ListarClientes
from cadastro_cliente.domain.cliente import Cliente
from cadastro_cliente.domain.erros import DadosInvalidosError
from tests.fabricas import payload_cliente
from tests.unit.application.fakes import RepositorioClienteEmMemoria


def _repo(n: int) -> RepositorioClienteEmMemoria:
    return RepositorioClienteEmMemoria(
        [Cliente.criar(**payload_cliente(nome=f"Cliente {i:03d}")) for i in reversed(range(n))]
    )


def test_paginas_de_20_ordenadas_por_nome():
    caso = ListarClientes(_repo(45))
    p1, p3 = caso.executar(1), caso.executar(3)
    assert len(p1.itens) == 20 and len(p3.itens) == 5
    assert [c.nome for c in p1.itens] == [f"Cliente {i:03d}" for i in range(20)]
    assert (p1.total_itens, p1.total_paginas) == (45, 3)


def test_pagina_alem_da_ultima_vazia_com_totais():
    pagina = ListarClientes(_repo(45)).executar(99)
    assert pagina.itens == []
    assert (pagina.total_itens, pagina.total_paginas) == (45, 3)


def test_sem_clientes():
    pagina = ListarClientes(_repo(0)).executar(1)
    assert (pagina.itens, pagina.total_itens, pagina.total_paginas) == ([], 0, 0)


@pytest.mark.parametrize("pagina", [0, -1])
def test_pagina_invalida(pagina):
    with pytest.raises(DadosInvalidosError) as exc:
        ListarClientes(_repo(1)).executar(pagina)
    assert exc.value.erros[0].field == "page"
