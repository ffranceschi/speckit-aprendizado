import pytest

from cadastro_cliente.domain.contato import Email, Telefone
from cadastro_cliente.domain.erros import DadosInvalidosError


def _codigo(cls, entrada):
    with pytest.raises(DadosInvalidosError) as exc:
        cls(entrada)
    return exc.value.erros[0].field, exc.value.erros[0].code


def test_email_normalizado():
    assert Email("  Maria@Example.com ").valor == "maria@example.com"


@pytest.mark.parametrize("entrada", ["joao@", "joao", "jo ao@x.com", "a@@b.com", "a@b", "a@.com"])
def test_email_invalido(entrada):
    assert _codigo(Email, entrada) == ("email", "email_invalido")


def test_email_obrigatorio_e_tamanho():
    assert _codigo(Email, "   ") == ("email", "obrigatorio")
    assert _codigo(Email, "a" * 250 + "@x.com") == ("email", "tamanho_invalido")


def test_email_repr_nao_expoe_valor():
    assert "maria" not in repr(Email("maria@example.com"))


@pytest.mark.parametrize(
    ("entrada", "formatado"),
    [("(11) 98765-4321", "(11) 98765-4321"), ("1134567890", "(11) 3456-7890")],
)
def test_telefone_valido(entrada, formatado):
    assert Telefone(entrada).formatado() == formatado


@pytest.mark.parametrize(
    "entrada", ["123456789", "123456789012", "(01) 98765-4321", "0912345678", "(11) 9876-ABCD"]
)
def test_telefone_invalido(entrada):
    assert _codigo(Telefone, entrada) == ("telefone", "telefone_invalido")


def test_telefone_obrigatorio_e_repr():
    assert _codigo(Telefone, "") == ("telefone", "obrigatorio")
    assert "98765" not in repr(Telefone("11987654321"))
