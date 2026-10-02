"""SC-005 / FR-018: nenhum dado pessoal em logs durante o fluxo completo, incluindo erros."""

from uuid import uuid4

import pytest

from tests.fabricas import gerar_cnpj, payload_cliente

pytestmark = pytest.mark.integration


def test_fluxo_completo_sem_dados_pessoais_nos_logs(client, logs_sem_dados_pessoais):
    a = logs_sem_dados_pessoais(payload_cliente())
    b = logs_sem_dados_pessoais(payload_cliente(documento=gerar_cnpj(formatado=True)))

    id_a = client.post("/clientes", json=a).json()["id"]
    id_b = client.post("/clientes", json=b).json()["id"]
    assert client.post("/clientes", json=a).status_code == 409
    assert client.post("/clientes", json={**a, "email": "x@"}).status_code == 422
    assert client.post("/clientes", json={**a, "nome": ["lista"]}).status_code == 422
    assert client.get("/clientes").status_code == 200
    assert client.get(f"/clientes/{id_a}").status_code == 200
    assert (
        client.put(f"/clientes/{id_a}", json={**a, "documento": b["documento"]}).status_code == 409
    )
    assert (
        client.put(f"/clientes/{id_b}", json={**b, "email": "novo@example.com"}).status_code == 200
    )
    assert client.delete(f"/clientes/{id_a}").status_code == 204
    assert client.delete(f"/clientes/{uuid4()}").status_code == 404
