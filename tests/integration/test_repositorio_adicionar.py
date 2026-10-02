import pytest
from sqlalchemy import text

from cadastro_cliente.domain.cliente import Cliente
from cadastro_cliente.domain.documento import Documento
from cadastro_cliente.domain.erros import DocumentoDuplicadoError
from cadastro_cliente.infrastructure.db.repositorio_cliente import RepositorioClienteSQL
from tests.fabricas import gerar_cpf, payload_cliente

pytestmark = pytest.mark.integration


def test_adicionar_grava_cifrado(repositorio, sessao):
    dados = payload_cliente(documento=gerar_cpf())
    cliente = Cliente.criar(**dados)
    repositorio.adicionar(cliente)
    sessao.commit()
    linha = sessao.execute(text("SELECT * FROM clientes")).mappings().one()
    for coluna in ("documento_cifrado", "email_cifrado", "telefone_cifrado", "endereco_cifrado"):
        bruto = bytes(linha[coluna])
        assert dados["documento"].encode() not in bruto
        assert dados["email"].encode() not in bruto
        assert dados["endereco"]["logradouro"].encode() not in bruto
    assert len(bytes(linha["documento_hash"])) == 32
    assert linha["tipo_pessoa"] == "FISICA"


def test_existe_documento_por_hash(repositorio):
    cpf = gerar_cpf(formatado=True)
    cliente = Cliente.criar(**payload_cliente(documento=cpf))
    repositorio.adicionar(cliente)
    assert repositorio.existe_documento(Documento(cpf.replace(".", "")))
    assert not repositorio.existe_documento(Documento(cpf), ignorar_id=cliente.id)
    assert not repositorio.existe_documento(Documento(gerar_cpf()))


def test_unicidade_garantida_pela_constraint(fabrica_sessoes, protetor):
    """Simula dois cadastros simultâneos: a checagem prévia passa nos dois, o banco barra um."""
    cpf = gerar_cpf()
    with fabrica_sessoes() as s1, fabrica_sessoes() as s2:
        r1, r2 = RepositorioClienteSQL(s1, protetor), RepositorioClienteSQL(s2, protetor)
        assert not r1.existe_documento(Documento(cpf))
        assert not r2.existe_documento(Documento(cpf))
        r1.adicionar(Cliente.criar(**payload_cliente(documento=cpf)))
        s1.commit()
        with pytest.raises(DocumentoDuplicadoError):
            r2.adicionar(Cliente.criar(**payload_cliente(documento=cpf)))
            s2.commit()
    with fabrica_sessoes() as s:
        assert s.execute(text("SELECT count(*) FROM clientes")).scalar() == 1
