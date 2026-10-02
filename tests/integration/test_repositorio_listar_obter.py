from uuid import uuid4

import pytest

from cadastro_cliente.domain.cliente import Cliente
from tests.fabricas import payload_cliente

pytestmark = pytest.mark.integration


def test_listar_ordenado_paginado(repositorio):
    for i in reversed(range(25)):
        repositorio.adicionar(Cliente.criar(**payload_cliente(nome=f"Nome {i:02d}")))
    p1, p2 = repositorio.listar(1, 20), repositorio.listar(2, 20)
    assert [c.nome for c in p1.itens] == [f"Nome {i:02d}" for i in range(20)]
    assert len(p2.itens) == 5
    assert (p1.total_itens, p1.total_paginas) == (25, 2)
    assert repositorio.listar(9, 20).itens == []


def test_nomes_iguais_ordem_estavel_por_id(repositorio):
    clientes = [Cliente.criar(**payload_cliente(nome="Mesmo Nome")) for _ in range(5)]
    for c in clientes:
        repositorio.adicionar(c)
    ids = [c.id for c in repositorio.listar(1, 20).itens]
    assert ids == sorted(c.id for c in clientes)
    assert ids == [c.id for c in repositorio.listar(1, 20).itens]


def test_obter_decifra_tudo(repositorio):
    dados = payload_cliente()
    original = Cliente.criar(**dados)
    repositorio.adicionar(original)
    lido = repositorio.obter(original.id)
    assert lido.documento == original.documento
    assert lido.email == original.email
    assert lido.telefone == original.telefone
    assert lido.endereco == original.endereco
    assert lido.nome == original.nome
    assert lido.criado_em == original.criado_em


def test_obter_inexistente(repositorio):
    assert repositorio.obter(uuid4()) is None
