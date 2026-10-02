from uuid import uuid4

import pytest

from cadastro_cliente.application.casos_de_uso.obter_cliente import ObterCliente
from cadastro_cliente.domain.cliente import Cliente
from cadastro_cliente.domain.erros import ClienteNaoEncontradoError
from tests.fabricas import payload_cliente
from tests.unit.application.fakes import RepositorioClienteEmMemoria


def test_obtem_existente():
    cliente = Cliente.criar(**payload_cliente())
    assert ObterCliente(RepositorioClienteEmMemoria([cliente])).executar(cliente.id) == cliente


def test_inexistente():
    with pytest.raises(ClienteNaoEncontradoError):
        ObterCliente(RepositorioClienteEmMemoria()).executar(uuid4())
