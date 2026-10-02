"""Fixtures compartilhadas. Testes de integração/contrato usam PostgreSQL real (testcontainers)."""

import logging
import os
from collections.abc import Iterator
from pathlib import Path

import pytest
from alembic import command
from alembic.config import Config
from fastapi.testclient import TestClient
from sqlalchemy import Engine, text
from sqlalchemy.orm import Session, sessionmaker

from cadastro_cliente.domain.cliente import Cliente
from cadastro_cliente.infrastructure.db.repositorio_cliente import RepositorioClienteSQL
from cadastro_cliente.infrastructure.db.sessao import (
    criar_engine,
    obter_sessao,
    sessao_transacional,
)
from cadastro_cliente.infrastructure.seguranca.protetor_dados import ProtetorDadosAesGcm
from cadastro_cliente.interfaces.api.dependencias import obter_protetor
from tests.fabricas import payload_cliente, valores_sensiveis

RAIZ = Path(__file__).resolve().parent.parent


@pytest.fixture(scope="session")
def database_url() -> Iterator[str]:
    """PostgreSQL de teste: TEST_DATABASE_URL, se definido, senão um container descartável."""
    url = os.environ.get("TEST_DATABASE_URL")
    if url:
        yield url
        return
    from testcontainers.postgres import PostgresContainer

    with PostgresContainer("postgres:16", driver="psycopg") as pg:
        yield pg.get_connection_url()


@pytest.fixture(scope="session")
def engine(database_url: str) -> Iterator[Engine]:
    cfg = Config(str(RAIZ / "alembic.ini"))
    cfg.set_main_option("script_location", str(RAIZ / "migrations"))
    cfg.set_main_option("sqlalchemy.url", database_url)
    cfg.attributes["configure_logger"] = False
    command.upgrade(cfg, "head")
    eng = criar_engine(database_url)
    yield eng
    eng.dispose()


@pytest.fixture
def fabrica_sessoes(engine: Engine) -> Iterator[sessionmaker[Session]]:
    yield sessionmaker(bind=engine, expire_on_commit=False)
    with engine.begin() as conn:
        conn.execute(text("TRUNCATE clientes"))


@pytest.fixture
def sessao(fabrica_sessoes: sessionmaker[Session]) -> Iterator[Session]:
    with fabrica_sessoes() as s:
        yield s
        s.rollback()


@pytest.fixture(scope="session")
def protetor() -> ProtetorDadosAesGcm:
    return ProtetorDadosAesGcm(os.urandom(32), os.urandom(32))


@pytest.fixture
def repositorio(sessao: Session, protetor: ProtetorDadosAesGcm) -> RepositorioClienteSQL:
    return RepositorioClienteSQL(sessao, protetor)


@pytest.fixture
def client(fabrica_sessoes: sessionmaker[Session], protetor) -> Iterator[TestClient]:
    from cadastro_cliente.main import criar_app

    app = criar_app()
    app.dependency_overrides[obter_sessao] = lambda: (
        yield from sessao_transacional(fabrica_sessoes)
    )
    app.dependency_overrides[obter_protetor] = lambda: protetor
    with TestClient(app, raise_server_exceptions=False) as c:
        yield c


@pytest.fixture
def cliente_cadastrado(fabrica_sessoes: sessionmaker[Session], protetor):
    """Grava um cliente direto pelo repositório (stories testáveis sem depender do POST)."""

    def _criar(**sobrescritas) -> tuple[Cliente, dict]:
        dados = payload_cliente(**sobrescritas)
        cliente = Cliente.criar(**dados)
        with fabrica_sessoes() as s:
            RepositorioClienteSQL(s, protetor).adicionar(cliente)
            s.commit()
        return cliente, dados

    return _criar


@pytest.fixture
def logs_sem_dados_pessoais(caplog):
    """Falha o teste se algum dado pessoal vigiado aparecer em qualquer log (FR-018, SC-005).

    Inclui nome e endereço (Constituição, Princípio IV: "demais dados pessoais").
    """
    caplog.set_level(logging.DEBUG)
    vigiados: set[str] = set()

    def vigiar(payload: dict) -> dict:
        vigiados.update(v for v in valores_sensiveis(payload) if v)
        return payload

    yield vigiar

    # Em teardown, caplog.records/text só enxergam a fase atual: inspecionar setup e call.
    registros = caplog.get_records("setup") + caplog.get_records("call")
    textos = [r.getMessage() for r in registros]
    textos += [str(vars(r)) for r in registros]
    for valor in vigiados:
        for texto in textos:
            assert valor not in texto, "dado pessoal encontrado nos logs"
