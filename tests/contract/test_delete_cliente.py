from uuid import uuid4

import pytest

pytestmark = pytest.mark.integration


def test_204_remove_e_libera_documento(client, cliente_cadastrado, logs_sem_dados_pessoais):
    cliente, dados = cliente_cadastrado()
    logs_sem_dados_pessoais(dados)
    r = client.delete(f"/clientes/{cliente.id}")
    assert r.status_code == 204
    assert r.content == b""
    assert client.get(f"/clientes/{cliente.id}").status_code == 404
    assert client.post("/clientes", json=dados).status_code == 201


def test_404(client):
    r = client.delete(f"/clientes/{uuid4()}")
    assert r.status_code == 404
    assert r.json()["errors"][0]["code"] == "cliente_nao_encontrado"
