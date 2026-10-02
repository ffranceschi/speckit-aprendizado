"""Engine e sessão SQLAlchemy."""

from collections.abc import Iterator
from functools import lru_cache

from sqlalchemy import Engine, create_engine
from sqlalchemy.orm import Session, sessionmaker

from cadastro_cliente.infrastructure.config import get_settings


def criar_engine(database_url: str) -> Engine:
    # hide_parameters: valores de SQL (ex.: nome) nunca aparecem em mensagens de erro/log.
    return create_engine(database_url, pool_pre_ping=True, hide_parameters=True)


@lru_cache
def _fabrica_sessoes() -> sessionmaker[Session]:
    return sessionmaker(bind=criar_engine(get_settings().database_url), expire_on_commit=False)


def sessao_transacional(fabrica: sessionmaker[Session]) -> Iterator[Session]:
    """Uma transação por requisição: commit em sucesso, rollback em qualquer erro."""
    with fabrica() as sessao:
        try:
            yield sessao
            sessao.commit()
        except Exception:
            sessao.rollback()
            raise


def obter_sessao() -> Iterator[Session]:
    yield from sessao_transacional(_fabrica_sessoes())
