from uuid import uuid4

import pytest

from tests.fabricas import gerar_cnpj

pytestmark = pytest.mark.integration


def test_detalhe_completo(client, cliente_cadastrado, logs_sem_dados_pessoais):
    cliente, dados = cliente_cadastrado(documento=gerar_cnpj())
    logs_sem_dados_pessoais(dados)
    r = client.get(f"/clientes/{cliente.id}")
    assert r.status_code == 200
    corpo = r.json()
    assert corpo["documento"] == cliente.documento.formatado()
    assert corpo["tipo_pessoa"] == "JURIDICA"
    assert corpo["email"] == dados["email"]
    assert corpo["endereco"]["logradouro"] == dados["endereco"]["logradouro"]


def test_404(client):
    r = client.get(f"/clientes/{uuid4()}")
    assert r.status_code == 404
    assert r.json()["errors"] == [
        {"field": None, "code": "cliente_nao_encontrado", "message": "Cliente não encontrado."}
    ]


def test_id_invalido(client):
    assert client.get("/clientes/nao-e-uuid").status_code == 422
