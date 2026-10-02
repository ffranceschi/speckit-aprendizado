import pytest

pytestmark = pytest.mark.integration


def test_lista_paginada_com_documento_mascarado(
    client, cliente_cadastrado, logs_sem_dados_pessoais
):
    for i in range(3):
        _, dados = cliente_cadastrado(nome=f"Cliente {2 - i}")
        logs_sem_dados_pessoais(dados)
    r = client.get("/clientes")
    assert r.status_code == 200
    corpo = r.json()
    assert (corpo["page"], corpo["page_size"], corpo["total_items"], corpo["total_pages"]) == (
        1,
        20,
        3,
        1,
    )
    assert [c["nome"] for c in corpo["items"]] == ["Cliente 0", "Cliente 1", "Cliente 2"]
    item = corpo["items"][0]
    assert set(item) == {"id", "nome", "documento_mascarado", "tipo_pessoa", "email", "telefone"}
    assert item["documento_mascarado"].startswith("***.") and item["documento_mascarado"].endswith(
        "-**"
    )


def test_lista_vazia(client):
    corpo = client.get("/clientes").json()
    assert corpo["items"] == [] and corpo["total_items"] == 0 and corpo["total_pages"] == 0


def test_pagina_alem_da_ultima(client, cliente_cadastrado):
    cliente_cadastrado()
    r = client.get("/clientes", params={"page": 99})
    assert r.status_code == 200
    assert r.json()["items"] == [] and r.json()["total_items"] == 1


@pytest.mark.parametrize("page", ["0", "-1", "abc"])
def test_pagina_invalida(client, page):
    r = client.get("/clientes", params={"page": page})
    assert r.status_code == 422
    assert r.json()["errors"][0]["field"] == "page"
