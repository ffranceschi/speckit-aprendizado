import pytest

from cadastro_cliente.domain.endereco import UFS, Endereco
from cadastro_cliente.domain.erros import DadosInvalidosError
from tests.fabricas import endereco_valido


def _erros(**dados):
    with pytest.raises(DadosInvalidosError) as exc:
        Endereco.criar(**dados)
    return {(e.field, e.code) for e in exc.value.erros}


def test_endereco_valido_normaliza():
    e = Endereco.criar(**endereco_valido(uf="sp", cep="01001000", complemento="  "))
    assert e.uf == "SP"
    assert e.cep == "01001000"
    assert e.cep_formatado() == "01001-000"
    assert e.complemento is None


def test_numero_aceita_sn():
    assert Endereco.criar(**endereco_valido(numero="S/N")).numero == "S/N"


def test_27_ufs():
    assert len(UFS) == 27


def test_todos_os_erros_juntos():
    erros = _erros(logradouro="", numero=None, bairro=" ", cidade="", uf="XX", cep="123")
    assert erros == {
        ("endereco.logradouro", "obrigatorio"),
        ("endereco.numero", "obrigatorio"),
        ("endereco.bairro", "obrigatorio"),
        ("endereco.cidade", "obrigatorio"),
        ("endereco.uf", "uf_invalida"),
        ("endereco.cep", "cep_invalido"),
    }


def test_obrigatorios_uf_cep():
    assert _erros(**endereco_valido(uf="", cep="")) == {
        ("endereco.uf", "obrigatorio"),
        ("endereco.cep", "obrigatorio"),
    }


@pytest.mark.parametrize(
    ("campo", "tamanho"),
    [("logradouro", 201), ("numero", 21), ("complemento", 101), ("bairro", 101), ("cidade", 101)],
)
def test_tamanhos_maximos(campo, tamanho):
    assert _erros(**endereco_valido(**{campo: "x" * tamanho})) == {
        (f"endereco.{campo}", "tamanho_invalido")
    }


def test_dict_ida_e_volta_e_repr():
    e = Endereco.criar(**endereco_valido())
    assert Endereco.criar(**e.para_dict()) == e
    assert "Flores" not in repr(e)
