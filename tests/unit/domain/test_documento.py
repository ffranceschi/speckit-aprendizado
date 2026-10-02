import pytest

from cadastro_cliente.domain.documento import Documento, TipoPessoa
from cadastro_cliente.domain.erros import DadosInvalidosError
from tests.fabricas import gerar_cnpj, gerar_cpf


def _codigo(entrada):
    with pytest.raises(DadosInvalidosError) as exc:
        Documento(entrada)
    assert exc.value.erros[0].field == "documento"
    return exc.value.erros[0].code


def test_pontuacao_e_ignorada():
    a, b = Documento("529.982.247-25"), Documento("52998224725")
    assert a == b
    assert hash(a) == hash(b)
    assert a.valor == "52998224725"


def test_tipo_derivado_do_tamanho():
    assert Documento(gerar_cpf()).tipo is TipoPessoa.FISICA
    assert Documento(gerar_cnpj()).tipo is TipoPessoa.JURIDICA


@pytest.mark.parametrize("_", range(20))
def test_documentos_gerados_sao_validos(_):
    Documento(gerar_cpf(formatado=True))
    Documento(gerar_cnpj(formatado=True))


@pytest.mark.parametrize(
    "entrada",
    [
        "123",
        "1234567890123",  # 13 dígitos
        "123456789012345",  # 15 dígitos
        "000.000.000-00",
        "111.111.111-11",
        "00000000000000",
        "529.982.247-26",  # DV incorreto
        "11.222.333/0001-82",  # DV incorreto
        "529.982.247-2A",
    ],
)
def test_documentos_invalidos(entrada):
    assert _codigo(entrada) == "documento_invalido"


@pytest.mark.parametrize("entrada", [None, "", "   "])
def test_documento_obrigatorio(entrada):
    assert _codigo(entrada) == "obrigatorio"


def test_formatado_e_mascarado():
    cpf, cnpj = Documento("52998224725"), Documento("11222333000181")
    assert cpf.formatado() == "529.982.247-25"
    assert cnpj.formatado() == "11.222.333/0001-81"
    assert cpf.mascarado() == "***.982.247-**"
    assert cnpj.mascarado() == "**.222.333/0001-**"


def test_repr_e_str_sao_mascarados():
    doc = Documento("529.982.247-25")
    assert "52998224725" not in repr(doc)
    assert "529.982.247-25" not in str(doc)
    assert str(doc) == "***.982.247-**"
