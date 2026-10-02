from uuid import uuid4

import pytest

from cadastro_cliente.application.casos_de_uso.criar_cliente import CriarCliente
from cadastro_cliente.application.casos_de_uso.remover_cliente import RemoverCliente
from cadastro_cliente.application.dto import DadosCliente, DadosEndereco
from cadastro_cliente.domain.cliente import Cliente
from cadastro_cliente.domain.erros import ClienteNaoEncontradoError
from tests.fabricas import payload_cliente
from tests.unit.application.fakes import RepositorioClienteEmMemoria


def test_remove_existente():
    cliente = Cliente.criar(**payload_cliente())
    repo = RepositorioClienteEmMemoria([cliente])
    RemoverCliente(repo).executar(cliente.id)
    assert repo.obter(cliente.id) is None


def test_inexistente():
    with pytest.raises(ClienteNaoEncontradoError):
        RemoverCliente(RepositorioClienteEmMemoria()).executar(uuid4())


def test_documento_liberado_apos_remocao():
    dados = payload_cliente()
    cliente = Cliente.criar(**dados)
    repo = RepositorioClienteEmMemoria([cliente])
    RemoverCliente(repo).executar(cliente.id)
    dto = DadosCliente(**{**dados, "endereco": DadosEndereco(**dados["endereco"])})
    assert CriarCliente(repo).executar(dto).documento == cliente.documento
