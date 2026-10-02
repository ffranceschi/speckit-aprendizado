from uuid import uuid4

import pytest
from sqlalchemy import text

from cadastro_cliente.domain.cliente import Cliente
from tests.fabricas import payload_cliente

pytestmark = pytest.mark.integration


def test_remocao_fisica_e_reinsercao(repositorio, sessao):
    dados = payload_cliente()
    cliente = Cliente.criar(**dados)
    repositorio.adicionar(cliente)
    assert repositorio.remover(cliente.id) is True
    restantes = sessao.execute(
        text("SELECT count(*) FROM clientes WHERE id = :id"), {"id": cliente.id}
    ).scalar()
    assert restantes == 0
    assert sessao.execute(text("SELECT count(*) FROM clientes")).scalar() == 0
    repositorio.adicionar(Cliente.criar(**dados))
    assert sessao.execute(text("SELECT count(*) FROM clientes")).scalar() == 1


def test_remover_inexistente(repositorio):
    assert repositorio.remover(uuid4()) is False
