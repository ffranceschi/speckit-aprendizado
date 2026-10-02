"""Injeção de dependências: monta repositório e protetor de dados por requisição."""

from functools import lru_cache
from typing import Annotated

from fastapi import Depends
from sqlalchemy.orm import Session

from cadastro_cliente.application.portas import ClienteRepository, ProtetorDados
from cadastro_cliente.infrastructure.config import get_settings
from cadastro_cliente.infrastructure.db.repositorio_cliente import RepositorioClienteSQL
from cadastro_cliente.infrastructure.db.sessao import obter_sessao
from cadastro_cliente.infrastructure.seguranca.protetor_dados import ProtetorDadosAesGcm


@lru_cache
def obter_protetor() -> ProtetorDados:
    settings = get_settings()
    return ProtetorDadosAesGcm(settings.cadastro_encryption_key, settings.cadastro_hmac_key)


def obter_repositorio(
    # scope="function": commit/rollback acontecem ANTES de a resposta ser enviada.
    sessao: Annotated[Session, Depends(obter_sessao, scope="function")],
    protetor: Annotated[ProtetorDados, Depends(obter_protetor)],
) -> ClienteRepository:
    return RepositorioClienteSQL(sessao, protetor)


Repositorio = Annotated[ClienteRepository, Depends(obter_repositorio)]
