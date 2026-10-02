"""Value object Documento: CPF ou CNPJ em campo único (FR-002 a FR-004, Princípio III)."""

import re
from enum import StrEnum

from cadastro_cliente.domain.erros import DadosInvalidosError, ErroCampo, erro_obrigatorio

_CARACTERES_PERMITIDOS = re.compile(r"^[\d.\-/\s]+$")
_PESOS_CNPJ = [6, 5, 4, 3, 2, 9, 8, 7, 6, 5, 4, 3, 2]


class TipoPessoa(StrEnum):
    FISICA = "FISICA"
    JURIDICA = "JURIDICA"


def _dv_cpf(digitos: list[int]) -> int:
    peso = len(digitos) + 1
    soma = sum(d * (peso - i) for i, d in enumerate(digitos))
    return (soma * 10) % 11 % 10


def _dv_cnpj(digitos: list[int]) -> int:
    pesos = _PESOS_CNPJ[-len(digitos) :]
    resto = sum(d * p for d, p in zip(digitos, pesos, strict=True)) % 11
    return 0 if resto < 2 else 11 - resto


def _dvs_corretos(valor: str, calcular) -> bool:
    digitos = [int(c) for c in valor]
    base = digitos[:-2]
    primeiro = calcular(base)
    segundo = calcular([*base, primeiro])
    return digitos[-2:] == [primeiro, segundo]


class Documento:
    __slots__ = ("_valor", "_tipo")

    def __init__(self, entrada: str | None):
        texto = (entrada or "").strip()
        if not texto:
            raise DadosInvalidosError([erro_obrigatorio("documento")])
        valor = re.sub(r"\D", "", texto)
        tipo = {11: TipoPessoa.FISICA, 14: TipoPessoa.JURIDICA}.get(len(valor))
        valido = (
            _CARACTERES_PERMITIDOS.match(texto) is not None
            and tipo is not None
            and len(set(valor)) > 1
            and _dvs_corretos(valor, _dv_cpf if tipo is TipoPessoa.FISICA else _dv_cnpj)
        )
        if not valido:
            raise DadosInvalidosError(
                [ErroCampo("documento", "documento_invalido", "Documento inválido.")]
            )
        self._valor = valor
        self._tipo = tipo

    @property
    def valor(self) -> str:
        return self._valor

    @property
    def tipo(self) -> TipoPessoa:
        return self._tipo

    def formatado(self) -> str:
        d = self._valor
        if self._tipo is TipoPessoa.FISICA:
            return f"{d[:3]}.{d[3:6]}.{d[6:9]}-{d[9:]}"
        return f"{d[:2]}.{d[2:5]}.{d[5:8]}/{d[8:12]}-{d[12:]}"

    def mascarado(self) -> str:
        d = self._valor
        if self._tipo is TipoPessoa.FISICA:
            return f"***.{d[3:6]}.{d[6:9]}-**"
        return f"**.{d[2:5]}.{d[5:8]}/{d[8:12]}-**"

    def __eq__(self, outro: object) -> bool:
        return isinstance(outro, Documento) and outro._valor == self._valor

    def __hash__(self) -> int:
        return hash(self._valor)

    def __str__(self) -> str:
        return self.mascarado()

    def __repr__(self) -> str:
        return f"Documento({self.mascarado()})"
