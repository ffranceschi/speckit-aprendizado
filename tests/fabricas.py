"""Fábricas de dados fictícios para testes (Constituição, Princípio IV: nunca dados reais)."""

import random

# Apenas para documentação/exemplos; os testes devem preferir gerar_cpf()/gerar_cnpj().
CPF_VALIDO = "529.982.247-25"
CNPJ_VALIDO = "11.222.333/0001-81"


def _dv_cpf(digitos: list[int]) -> int:
    peso = len(digitos) + 1
    soma = sum(d * (peso - i) for i, d in enumerate(digitos))
    return (soma * 10) % 11 % 10


def _dv_cnpj(digitos: list[int]) -> int:
    pesos = [6, 5, 4, 3, 2, 9, 8, 7, 6, 5, 4, 3, 2][-len(digitos) :]
    resto = sum(d * p for d, p in zip(digitos, pesos, strict=True)) % 11
    return 0 if resto < 2 else 11 - resto


def gerar_cpf(formatado: bool = False) -> str:
    while True:
        base = [random.randint(0, 9) for _ in range(9)]
        if len(set(base)) > 1:
            break
    base.append(_dv_cpf(base))
    base.append(_dv_cpf(base))
    d = "".join(map(str, base))
    return f"{d[:3]}.{d[3:6]}.{d[6:9]}-{d[9:]}" if formatado else d


def gerar_cnpj(formatado: bool = False) -> str:
    while True:
        base = [random.randint(0, 9) for _ in range(8)] + [0, 0, 0, 1]
        if len(set(base)) > 1:
            break
    base.append(_dv_cnpj(base))
    base.append(_dv_cnpj(base))
    d = "".join(map(str, base))
    return f"{d[:2]}.{d[2:5]}.{d[5:8]}/{d[8:12]}-{d[12:]}" if formatado else d


def gerar_telefone() -> str:
    return f"(11) 9{random.randint(1000, 9999)}-{random.randint(1000, 9999)}"


def endereco_valido(**sobrescritas) -> dict:
    endereco = {
        "logradouro": "Rua das Flores",
        "numero": "123",
        "complemento": "Apto 42",
        "bairro": "Centro",
        "cidade": "São Paulo",
        "uf": "SP",
        "cep": "01001-000",
    }
    endereco.update(sobrescritas)
    return endereco


def payload_cliente(**sobrescritas) -> dict:
    """Dict completo no formato ClienteEntrada (contracts/openapi.yaml)."""
    n = random.randint(1000, 9999)
    payload = {
        "nome": f"Cliente Teste {n}",
        "documento": gerar_cpf(formatado=True),
        "email": f"cliente{n}@example.com",
        "telefone": gerar_telefone(),
        "endereco": endereco_valido(),
    }
    payload.update(sobrescritas)
    return payload


def valores_sensiveis(payload: dict) -> list[str]:
    """Valores pessoais de um payload que nunca podem aparecer em logs."""
    digitos = lambda s: "".join(c for c in s if c.isdigit())  # noqa: E731
    end = payload["endereco"]
    return [
        payload["nome"],
        payload["documento"],
        digitos(payload["documento"]),
        payload["email"],
        payload["telefone"],
        digitos(payload["telefone"]),
        end["logradouro"],
    ]
