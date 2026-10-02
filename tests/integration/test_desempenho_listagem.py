"""SC-004: primeira página em até 2 s com 10.000 clientes."""

import time

import pytest
from sqlalchemy import insert

from cadastro_cliente.domain.cliente import Cliente
from cadastro_cliente.infrastructure.db.modelos import ClienteModel
from cadastro_cliente.infrastructure.db.repositorio_cliente import RepositorioClienteSQL
from tests.fabricas import payload_cliente

pytestmark = pytest.mark.integration

TOTAL = 10_000


def test_primeira_pagina_com_10_mil_clientes(client, fabrica_sessoes, protetor):
    with fabrica_sessoes() as s:
        repo = RepositorioClienteSQL(s, protetor)
        linhas = []
        for i in range(TOTAL):
            modelo = repo._para_modelo(Cliente.criar(**payload_cliente(nome=f"Cliente {i:05d}")))
            linhas.append({c.name: getattr(modelo, c.key) for c in ClienteModel.__table__.columns})
        s.execute(insert(ClienteModel), linhas)
        s.commit()

    inicio = time.perf_counter()
    r = client.get("/clientes", params={"page": 1})
    duracao = time.perf_counter() - inicio

    assert r.status_code == 200
    assert r.json()["total_items"] == TOTAL
    assert duracao <= 2.0, f"listagem levou {duracao:.2f}s"
