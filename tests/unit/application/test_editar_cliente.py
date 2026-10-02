from uuid import uuid4

import pytest

from cadastro_cliente.application.casos_de_uso.editar_cliente import EditarCliente
from cadastro_cliente.application.dto import DadosCliente, DadosEndereco
from cadastro_cliente.domain.cliente import Cliente
from cadastro_cliente.domain.erros import (
    ClienteNaoEncontradoError,
    DadosInvalidosError,
    DocumentoDuplicadoError,
)
from tests.fabricas import payload_cliente
from tests.unit.application.fakes import RepositorioClienteEmMemoria


def _dto(p: dict) -> DadosCliente:
    return DadosCliente(**{**p, "endereco": DadosEndereco(**p["endereco"])})


@pytest.fixture
def cenario():
    dados_a, dados_b = payload_cliente(), payload_cliente()
    a, b = Cliente.criar(**dados_a), Cliente.criar(**dados_b)
    return RepositorioClienteEmMemoria([a, b]), a, dados_a, b, dados_b


def test_altera_email(cenario):
    repo, a, dados_a, *_ = cenario
    editado = EditarCliente(repo).executar(a.id, _dto({**dados_a, "email": "novo@example.com"}))
    assert repo.obter(a.id).email.valor == "novo@example.com"
    assert editado.criado_em == a.criado_em
    assert editado.atualizado_em >= a.atualizado_em


def test_manter_proprio_documento_nao_e_duplicidade(cenario):
    repo, a, dados_a, *_ = cenario
    EditarCliente(repo).executar(a.id, _dto({**dados_a, "nome": "Outro Nome"}))
    assert repo.obter(a.id).nome == "Outro Nome"


def test_documento_de_outro_cliente(cenario):
    repo, a, dados_a, _, dados_b = cenario
    with pytest.raises(DocumentoDuplicadoError):
        EditarCliente(repo).executar(a.id, _dto({**dados_a, "documento": dados_b["documento"]}))
    assert repo.obter(a.id).documento == a.documento


def test_email_invalido_mantem_dados(cenario):
    repo, a, dados_a, *_ = cenario
    with pytest.raises(DadosInvalidosError):
        EditarCliente(repo).executar(a.id, _dto({**dados_a, "email": "ruim@"}))
    assert repo.obter(a.id).email == a.email


def test_inexistente():
    with pytest.raises(ClienteNaoEncontradoError):
        EditarCliente(RepositorioClienteEmMemoria()).executar(uuid4(), _dto(payload_cliente()))
