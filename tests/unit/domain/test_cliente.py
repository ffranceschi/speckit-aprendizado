from datetime import UTC, datetime, timedelta
from uuid import UUID

import pytest

from cadastro_cliente.domain.cliente import Cliente
from cadastro_cliente.domain.documento import TipoPessoa
from cadastro_cliente.domain.erros import DadosInvalidosError
from tests.fabricas import endereco_valido, gerar_cnpj, payload_cliente


def test_criar_cliente_valido():
    dados = payload_cliente()
    c = Cliente.criar(**dados)
    assert isinstance(c.id, UUID) and c.id.version == 4
    assert c.tipo_pessoa is TipoPessoa.FISICA
    assert c.criado_em == c.atualizado_em
    assert c.criado_em.tzinfo is not None
    assert c.nome == dados["nome"]


def test_tipo_juridica():
    assert (
        Cliente.criar(**payload_cliente(documento=gerar_cnpj())).tipo_pessoa is TipoPessoa.JURIDICA
    )


@pytest.mark.parametrize("nome", ["", "   ", "A", "x" * 151])
def test_nome_invalido(nome):
    with pytest.raises(DadosInvalidosError) as exc:
        Cliente.criar(**payload_cliente(nome=nome))
    assert exc.value.erros[0].field == "nome"


def test_todos_os_erros_em_uma_excecao():
    dados = payload_cliente(
        nome="  ",
        documento="529.982.247-26",
        email="joao@",
        telefone="123",
        endereco=endereco_valido(cep=""),
    )
    with pytest.raises(DadosInvalidosError) as exc:
        Cliente.criar(**dados)
    assert {e.field for e in exc.value.erros} == {
        "nome",
        "documento",
        "email",
        "telefone",
        "endereco.cep",
    }


def test_atualizar_revalida_e_preserva_identidade():
    c = Cliente.criar(**payload_cliente())
    id_, criado = c.id, c.criado_em
    depois = criado + timedelta(seconds=5)
    novos = payload_cliente(email="novo@example.com")
    c.atualizar(**novos, agora=depois)
    assert c.id == id_ and c.criado_em == criado
    assert c.atualizado_em == depois
    assert c.email.valor == "novo@example.com"


def test_atualizar_invalido_nao_altera():
    dados = payload_cliente()
    c = Cliente.criar(**dados)
    with pytest.raises(DadosInvalidosError):
        c.atualizar(**payload_cliente(email="ruim@"), agora=datetime.now(UTC))
    assert c.email.valor == dados["email"]
    assert c.nome == dados["nome"]


def test_repr_sem_dados_pessoais():
    dados = payload_cliente()
    texto = repr(Cliente.criar(**dados))
    assert dados["nome"] not in texto
    assert dados["email"] not in texto
