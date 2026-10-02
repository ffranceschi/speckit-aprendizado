"""Value objects de contato: Email (FR-006) e Telefone (FR-007)."""

import re

from cadastro_cliente.domain.erros import DadosInvalidosError, ErroCampo, erro_obrigatorio

_EMAIL = re.compile(r"^[^\s@]+@(?:[^\s@.]+\.)+[^\s@.]+$")
_TELEFONE_CARACTERES = re.compile(r"^[\d()\-\s]+$")


class Email:
    __slots__ = ("_valor",)
    TAMANHO_MAXIMO = 254

    def __init__(self, entrada: str | None):
        texto = (entrada or "").strip()
        if not texto:
            raise DadosInvalidosError([erro_obrigatorio("email")])
        if len(texto) > self.TAMANHO_MAXIMO:
            raise DadosInvalidosError(
                [ErroCampo("email", "tamanho_invalido", "E-mail deve ter até 254 caracteres.")]
            )
        if not _EMAIL.match(texto):
            raise DadosInvalidosError([ErroCampo("email", "email_invalido", "E-mail inválido.")])
        self._valor = texto.lower()

    @property
    def valor(self) -> str:
        return self._valor

    def __eq__(self, outro: object) -> bool:
        return isinstance(outro, Email) and outro._valor == self._valor

    def __hash__(self) -> int:
        return hash(self._valor)

    def __repr__(self) -> str:
        return "Email(***)"


class Telefone:
    __slots__ = ("_valor",)

    def __init__(self, entrada: str | None):
        texto = (entrada or "").strip()
        if not texto:
            raise DadosInvalidosError([erro_obrigatorio("telefone")])
        valor = re.sub(r"\D", "", texto)
        valido = (
            _TELEFONE_CARACTERES.match(texto) is not None
            and len(valor) in (10, 11)
            and valor[0] != "0"
            and 11 <= int(valor[:2]) <= 99
        )
        if not valido:
            raise DadosInvalidosError(
                [
                    ErroCampo(
                        "telefone", "telefone_invalido", "Telefone inválido: informe DDD + número."
                    )
                ]
            )
        self._valor = valor

    @property
    def valor(self) -> str:
        return self._valor

    def formatado(self) -> str:
        d = self._valor
        return f"({d[:2]}) {d[2:-4]}-{d[-4:]}"

    def __eq__(self, outro: object) -> bool:
        return isinstance(outro, Telefone) and outro._valor == self._valor

    def __hash__(self) -> int:
        return hash(self._valor)

    def __repr__(self) -> str:
        return "Telefone(***)"
