from uuid import uuid4

import pytest

from tests.fabricas import gerar_cnpj, payload_cliente

pytestmark = pytest.mark.integration


def test_200_altera(client, cliente_cadastrado, logs_sem_dados_pessoais):
    cliente, dados = cliente_cadastrado()
    novo = logs_sem_dados_pessoais({**dados, "email": "novo@example.com"})
    r = client.put(f"/clientes/{cliente.id}", json=novo)
    assert r.status_code == 200
    assert r.json()["email"] == "novo@example.com"
    assert client.get(f"/clientes/{cliente.id}").json()["email"] == "novo@example.com"


def test_409_documento_de_outro_mantem_dados(client, cliente_cadastrado, logs_sem_dados_pessoais):
    a, dados_a = cliente_cadastrado()
    _, dados_b = cliente_cadastrado(documento=gerar_cnpj(formatado=True))
    logs_sem_dados_pessoais(dados_a)
    logs_sem_dados_pessoais(dados_b)
    r = client.put(f"/clientes/{a.id}", json={**dados_a, "documento": dados_b["documento"]})
    assert r.status_code == 409
    assert dados_b["documento"] not in r.text
    assert client.get(f"/clientes/{a.id}").json()["documento"] == a.documento.formatado()


def test_422_todos_os_erros_sem_input(client, cliente_cadastrado):
    cliente, dados = cliente_cadastrado()
    r = client.put(f"/clientes/{cliente.id}", json={**dados, "email": "ruim@", "telefone": "123"})
    assert r.status_code == 422
    assert {e["field"] for e in r.json()["errors"]} == {"email", "telefone"}
    assert "input" not in r.text
    assert client.get(f"/clientes/{cliente.id}").json()["email"] == dados["email"]


def test_404(client):
    assert client.put(f"/clientes/{uuid4()}", json=payload_cliente()).status_code == 404
