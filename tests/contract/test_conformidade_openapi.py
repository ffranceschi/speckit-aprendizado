"""O app expõe exatamente os paths, métodos e status documentados no contrato."""

from pathlib import Path

import yaml

from cadastro_cliente.main import criar_app

CONTRATO = Path(__file__).resolve().parents[2] / "specs/001-cadastro-cliente/contracts/openapi.yaml"
_METODOS = {"get", "post", "put", "delete", "patch"}


def _operacoes(doc: dict) -> dict[tuple[str, str], set[str]]:
    return {
        (path, metodo): set(op["responses"])
        for path, item in doc["paths"].items()
        for metodo, op in item.items()
        if metodo in _METODOS
    }


def test_paths_metodos_e_status_iguais_ao_contrato():
    contrato = _operacoes(yaml.safe_load(CONTRATO.read_text()))
    app = _operacoes(criar_app().openapi())
    assert set(app) == set(contrato)
    for chave, status in contrato.items():
        assert status <= app[chave], f"{chave}: faltam {status - app[chave]}"
