import pytest

from tests.fabricas import endereco_valido, gerar_cnpj, gerar_cpf, payload_cliente

pytestmark = pytest.mark.integration


def _campos(resposta):
    return {(e["field"], e["code"]) for e in resposta.json()["errors"]}


def test_201_pessoa_fisica(client, logs_sem_dados_pessoais):
    payload = logs_sem_dados_pessoais(payload_cliente(documento=gerar_cpf()))
    r = client.post("/clientes", json=payload)
    assert r.status_code == 201
    corpo = r.json()
    assert r.headers["location"] == f"/clientes/{corpo['id']}"
    assert corpo["tipo_pessoa"] == "FISICA"
    assert corpo["nome"] == payload["nome"]
    assert corpo["documento"].count(".") == 2 and "-" in corpo["documento"]
    assert corpo["endereco"]["cep"] == "01001-000"
    assert set(corpo) == {
        "id", "nome", "documento", "tipo_pessoa", "email", "telefone",
        "endereco", "criado_em", "atualizado_em",
    }  # fmt: skip


def test_201_pessoa_juridica(client, logs_sem_dados_pessoais):
    payload = logs_sem_dados_pessoais(payload_cliente(documento=gerar_cnpj(formatado=True)))
    r = client.post("/clientes", json=payload)
    assert r.status_code == 201
    assert r.json()["tipo_pessoa"] == "JURIDICA"


def test_409_duplicado_sem_expor_documento(client, logs_sem_dados_pessoais):
    cpf = gerar_cpf(formatado=True)
    digitos = cpf.replace(".", "").replace("-", "")
    primeiro = logs_sem_dados_pessoais(payload_cliente(documento=cpf))
    assert client.post("/clientes", json=primeiro).status_code == 201
    segundo = logs_sem_dados_pessoais(payload_cliente(documento=digitos))
    r = client.post("/clientes", json=segundo)
    assert r.status_code == 409
    assert _campos(r) == {("documento", "documento_duplicado")}
    assert digitos not in r.text and cpf not in r.text


def test_422_lista_todos_os_erros(client, logs_sem_dados_pessoais):
    payload = logs_sem_dados_pessoais(payload_cliente(documento="529.982.247-26", email="joao@"))
    r = client.post("/clientes", json=payload)
    assert r.status_code == 422
    assert _campos(r) == {("documento", "documento_invalido"), ("email", "email_invalido")}
    assert "529.982.247-26" not in r.text and "joao@" not in r.text


def test_422_digitos_iguais(client):
    r = client.post("/clientes", json=payload_cliente(documento="111.111.111-11"))
    assert r.status_code == 422
    assert _campos(r) == {("documento", "documento_invalido")}


def test_422_obrigatorios(client):
    endereco = endereco_valido()
    del endereco["cep"]
    r = client.post("/clientes", json=payload_cliente(nome="   ", endereco=endereco))
    assert r.status_code == 422
    assert _campos(r) == {("nome", "obrigatorio"), ("endereco.cep", "obrigatorio")}


def test_422_payload_malformado_sem_input(client, logs_sem_dados_pessoais):
    payload = logs_sem_dados_pessoais(payload_cliente())
    r = client.post("/clientes", json={**payload, "nome": {"x": payload["nome"]}})
    assert r.status_code == 422
    assert "input" not in r.text
    assert payload["nome"] not in r.text
    assert _campos(r) == {("nome", "formato_invalido")}
