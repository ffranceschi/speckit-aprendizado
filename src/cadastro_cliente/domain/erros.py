"""Erros de domínio. Mensagens nunca incluem o valor informado (Constituição, Princípio IV)."""

from dataclasses import dataclass, field


@dataclass(frozen=True)
class ErroCampo:
    field: str | None
    code: str
    message: str


class ErroDominio(Exception):
    """Base dos erros de negócio."""


class DadosInvalidosError(ErroDominio):
    def __init__(self, erros: list[ErroCampo]):
        super().__init__(f"{len(erros)} campo(s) inválido(s)")
        self.erros = list(erros)


class DocumentoDuplicadoError(ErroDominio):
    erro = ErroCampo("documento", "documento_duplicado", "Documento já cadastrado.")

    def __init__(self):
        super().__init__(self.erro.message)


class ClienteNaoEncontradoError(ErroDominio):
    erro = ErroCampo(None, "cliente_nao_encontrado", "Cliente não encontrado.")

    def __init__(self):
        super().__init__(self.erro.message)


def erro_obrigatorio(campo: str) -> ErroCampo:
    return ErroCampo(campo, "obrigatorio", "Campo obrigatório.")


@dataclass
class ColetorErros:
    """Acumula erros de vários campos para reportá-los juntos (FR-010)."""

    erros: list[ErroCampo] = field(default_factory=list)

    def adicionar(self, erro: ErroCampo) -> None:
        self.erros.append(erro)

    def texto(
        self,
        valor: str | None,
        campo: str,
        minimo: int,
        maximo: int,
        obrigatorio: bool = True,
    ) -> str | None:
        texto = (valor or "").strip()
        if not texto:
            if obrigatorio:
                self.adicionar(erro_obrigatorio(campo))
            return None
        if not minimo <= len(texto) <= maximo:
            self.adicionar(
                ErroCampo(
                    campo,
                    "tamanho_invalido",
                    f"Deve ter entre {minimo} e {maximo} caracteres.",
                )
            )
            return None
        return texto

    def tentar(self, fabrica, *args, **kwargs):
        try:
            return fabrica(*args, **kwargs)
        except DadosInvalidosError as exc:
            self.erros.extend(exc.erros)
            return None

    def verificar(self) -> None:
        if self.erros:
            raise DadosInvalidosError(self.erros)
