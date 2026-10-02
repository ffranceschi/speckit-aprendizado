"""Value object Endereco (FR-009): obrigatório e completo; complemento opcional."""

import re
from dataclasses import asdict, dataclass

from cadastro_cliente.domain.erros import ColetorErros, ErroCampo, erro_obrigatorio

UFS = frozenset(
    {
        "AC", "AL", "AP", "AM", "BA", "CE", "DF", "ES", "GO", "MA", "MT", "MS", "MG", "PA",
        "PB", "PR", "PE", "PI", "RJ", "RN", "RS", "RO", "RR", "SC", "SP", "SE", "TO",
    }
)  # fmt: skip


@dataclass(frozen=True, repr=False)
class Endereco:
    logradouro: str
    numero: str
    complemento: str | None
    bairro: str
    cidade: str
    uf: str
    cep: str

    @classmethod
    def criar(
        cls,
        *,
        logradouro: str | None,
        numero: str | None,
        bairro: str | None,
        cidade: str | None,
        uf: str | None,
        cep: str | None,
        complemento: str | None = None,
    ) -> "Endereco":
        c = ColetorErros()
        dados = {
            "logradouro": c.texto(logradouro, "endereco.logradouro", 1, 200),
            "numero": c.texto(numero, "endereco.numero", 1, 20),
            "complemento": c.texto(complemento, "endereco.complemento", 0, 100, obrigatorio=False),
            "bairro": c.texto(bairro, "endereco.bairro", 1, 100),
            "cidade": c.texto(cidade, "endereco.cidade", 1, 100),
        }

        uf_texto = (uf or "").strip().upper()
        if not uf_texto:
            c.adicionar(erro_obrigatorio("endereco.uf"))
        elif uf_texto not in UFS:
            c.adicionar(ErroCampo("endereco.uf", "uf_invalida", "UF inválida."))

        cep_texto = (cep or "").strip()
        cep_digitos = re.sub(r"\D", "", cep_texto)
        if not cep_texto:
            c.adicionar(erro_obrigatorio("endereco.cep"))
        elif len(cep_digitos) != 8 or not re.fullmatch(r"[\d.\-\s]+", cep_texto):
            c.adicionar(ErroCampo("endereco.cep", "cep_invalido", "CEP deve conter 8 dígitos."))

        c.verificar()
        return cls(**dados, uf=uf_texto, cep=cep_digitos)

    def cep_formatado(self) -> str:
        return f"{self.cep[:5]}-{self.cep[5:]}"

    def para_dict(self) -> dict[str, str | None]:
        return asdict(self)

    def __repr__(self) -> str:
        return "Endereco(***)"
