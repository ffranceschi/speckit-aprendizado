"""Dados de entrada dos casos de uso (strings cruas, validadas no domínio)."""

from dataclasses import asdict, dataclass

TAMANHO_PAGINA = 20


@dataclass(frozen=True, repr=False)
class DadosEndereco:
    logradouro: str | None
    numero: str | None
    bairro: str | None
    cidade: str | None
    uf: str | None
    cep: str | None
    complemento: str | None = None

    def __repr__(self) -> str:
        return "DadosEndereco(***)"


@dataclass(frozen=True, repr=False)
class DadosCliente:
    nome: str | None
    documento: str | None
    email: str | None
    telefone: str | None
    endereco: DadosEndereco | None

    def como_kwargs(self) -> dict:
        return {
            "nome": self.nome,
            "documento": self.documento,
            "email": self.email,
            "telefone": self.telefone,
            "endereco": asdict(self.endereco) if self.endereco else None,
        }

    def __repr__(self) -> str:
        # Nunca expor dados pessoais em logs/tracebacks (Princípio IV).
        return "DadosCliente(***)"
