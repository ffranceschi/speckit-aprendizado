import logging
import uuid

import pytest

from cadastro_cliente.infrastructure.logging.sanitizador import FiltroDadosSensiveis, mascarar


def _registro(msg, *args):
    return logging.LogRecord("t", logging.INFO, __file__, 1, msg, args, None)


@pytest.mark.parametrize(
    "sensivel",
    [
        "529.982.247-25",
        "52998224725",
        "11.222.333/0001-81",
        "11222333000181",
        "maria.silva@example.com",
        "(11) 98765-4321",
        "11987654321",
        "(11) 3456-7890",
    ],
)
def test_mascara_em_msg_e_args(sensivel):
    filtro = FiltroDadosSensiveis()
    r1 = _registro(f"valor={sensivel} fim")
    r2 = _registro("valor=%s fim", sensivel)
    for r in (r1, r2):
        assert filtro.filter(r) is True
        assert sensivel not in r.getMessage()
        assert r.getMessage().startswith("valor=") and r.getMessage().endswith(" fim")


def test_nao_altera_uuid_nem_texto_comum():
    id_ = "12345678-1234-1234-1234-123456789012"
    texto = f"cliente_criado id={id_} id2={uuid.uuid4()} pagina=3 total=45"
    assert mascarar(texto) == texto


def test_mascara_extras():
    r = _registro("evento")
    r.detalhe = "doc 52998224725"
    FiltroDadosSensiveis().filter(r)
    assert "52998224725" not in r.detalhe


def test_compativel_com_formatter_de_acesso_do_uvicorn():
    from uvicorn.logging import AccessFormatter

    r = logging.LogRecord(
        "uvicorn.access",
        logging.INFO,
        __file__,
        1,
        '%s - "%s %s HTTP/%s" %d',
        ("127.0.0.1:5000", "GET", "/clientes?doc=52998224725", "1.1", 200),
        None,
    )
    FiltroDadosSensiveis().filter(r)
    linha = AccessFormatter('%(client_addr)s - "%(request_line)s" %(status_code)s').format(r)
    assert "GET /clientes?doc=" in linha and "200" in linha
    assert "52998224725" not in linha
