"""Composição da aplicação FastAPI."""

from fastapi import FastAPI

from cadastro_cliente.infrastructure.logging.sanitizador import configurar_logging
from cadastro_cliente.interfaces.api.erros import registrar_tratadores
from cadastro_cliente.interfaces.api.rotas_clientes import router as rotas_clientes


def criar_app() -> FastAPI:
    configurar_logging()
    app = FastAPI(title="Cadastro de Cliente API", version="1.0.0")
    registrar_tratadores(app)
    app.include_router(rotas_clientes)
    return app


app = criar_app()
