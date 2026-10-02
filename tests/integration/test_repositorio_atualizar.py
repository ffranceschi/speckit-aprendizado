import pytest
from sqlalchemy import text

from cadastro_cliente.domain.cliente import Cliente
from cadastro_cliente.domain.erros import DocumentoDuplicadoError
from tests.fabricas import gerar_cnpj, payload_cliente

pytestmark = pytest.mark.integration


def _hash(sessao, id_):
    return bytes(
        sessao.execute(
            text("SELECT documento_hash FROM clientes WHERE id = :id"), {"id": id_}
        ).scalar_one()
    )


def test_atualizar_recifra_e_recalcula_hash(repositorio, sessao):
    dados = payload_cliente()
    cliente = Cliente.criar(**dados)
    repositorio.adicionar(cliente)
    antes = _hash(sessao, cliente.id)
    cliente.atualizar(**{**dados, "documento": gerar_cnpj(), "email": "novo@example.com"})
    repositorio.atualizar(cliente)
    assert _hash(sessao, cliente.id) != antes
    lido = repositorio.obter(cliente.id)
    assert lido.documento == cliente.documento
    assert lido.email.valor == "novo@example.com"


def test_atualizar_para_documento_de_outro(repositorio, sessao):
    dados_a, dados_b = payload_cliente(), payload_cliente()
    a, b = Cliente.criar(**dados_a), Cliente.criar(**dados_b)
    repositorio.adicionar(a)
    repositorio.adicionar(b)
    antes = _hash(sessao, a.id)
    a.atualizar(**{**dados_a, "documento": dados_b["documento"]})
    with pytest.raises(DocumentoDuplicadoError):
        repositorio.atualizar(a)
    assert _hash(sessao, a.id) == antes
