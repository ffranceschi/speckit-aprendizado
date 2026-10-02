import pytest

from cadastro_cliente.application.casos_de_uso.criar_cliente import CriarCliente
from cadastro_cliente.application.dto import DadosCliente, DadosEndereco
from cadastro_cliente.domain.documento import TipoPessoa
from cadastro_cliente.domain.erros import DadosInvalidosError, DocumentoDuplicadoError
from tests.fabricas import gerar_cnpj, gerar_cpf, payload_cliente
from tests.unit.application.fakes import RepositorioClienteEmMemoria


def dados(**sobrescritas) -> DadosCliente:
    p = payload_cliente(**sobrescritas)
    return DadosCliente(**{**p, "endereco": DadosEndereco(**p["endereco"])})


def test_cria_cpf_e_cnpj():
    repo = RepositorioClienteEmMemoria()
    pf = CriarCliente(repo).executar(dados(documento=gerar_cpf()))
    pj = CriarCliente(repo).executar(dados(documento=gerar_cnpj()))
    assert pf.tipo_pessoa is TipoPessoa.FISICA
    assert pj.tipo_pessoa is TipoPessoa.JURIDICA
    assert repo.obter(pf.id) == pf
    assert len(repo) == 2


def test_documento_duplicado_com_outra_pontuacao():
    repo = RepositorioClienteEmMemoria()
    cpf = gerar_cpf(formatado=True)
    CriarCliente(repo).executar(dados(documento=cpf))
    with pytest.raises(DocumentoDuplicadoError):
        CriarCliente(repo).executar(dados(documento=cpf.replace(".", "").replace("-", "")))
    assert len(repo) == 1


def test_dados_invalidos_reporta_todos_e_nao_grava():
    repo = RepositorioClienteEmMemoria()
    with pytest.raises(DadosInvalidosError) as exc:
        CriarCliente(repo).executar(dados(nome=" ", email="joao@", documento="529.982.247-26"))
    assert {e.field for e in exc.value.erros} == {"nome", "email", "documento"}
    assert len(repo) == 0


def test_log_sem_dados_pessoais(caplog):
    caplog.set_level("INFO")
    d = dados()
    cliente = CriarCliente(RepositorioClienteEmMemoria()).executar(d)
    registro = next(r for r in caplog.records if r.getMessage() == "cliente_criado")
    assert registro.cliente_id == str(cliente.id)
    tudo = caplog.text + str(vars(registro))
    for valor in (d.nome, d.documento, d.email, d.telefone):
        assert valor not in tudo
