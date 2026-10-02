"""Tradução de erros para HTTP no formato `Erros` (R12). Nunca ecoa valores informados (R7)."""

import logging

from fastapi import FastAPI, Request
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse

from cadastro_cliente.domain.erros import (
    ClienteNaoEncontradoError,
    DadosInvalidosError,
    DocumentoDuplicadoError,
    ErroCampo,
)

logger = logging.getLogger(__name__)

_LOCAIS = {"body", "query", "path"}


def _resposta(status: int, erros: list[ErroCampo]) -> JSONResponse:
    return JSONResponse(
        status_code=status,
        content={
            "errors": [{"field": e.field, "code": e.code, "message": e.message} for e in erros]
        },
    )


def _erro_de_validacao(detalhe: dict) -> ErroCampo:
    loc = [str(p) for p in detalhe.get("loc", ()) if p not in _LOCAIS]
    campo = ".".join(loc) or None
    if detalhe.get("type") == "missing":
        return ErroCampo(campo, "obrigatorio", "Campo obrigatório.")
    return ErroCampo(campo, "formato_invalido", "Formato inválido.")


def registrar_tratadores(app: FastAPI) -> None:
    @app.exception_handler(DadosInvalidosError)
    async def _dados_invalidos(_: Request, exc: DadosInvalidosError) -> JSONResponse:
        return _resposta(422, exc.erros)

    @app.exception_handler(DocumentoDuplicadoError)
    async def _duplicado(_: Request, exc: DocumentoDuplicadoError) -> JSONResponse:
        return _resposta(409, [exc.erro])

    @app.exception_handler(ClienteNaoEncontradoError)
    async def _nao_encontrado(_: Request, exc: ClienteNaoEncontradoError) -> JSONResponse:
        return _resposta(404, [exc.erro])

    @app.exception_handler(RequestValidationError)
    async def _validacao(_: Request, exc: RequestValidationError) -> JSONResponse:
        # Substitui o handler padrão, que inclui o campo `input` com o valor enviado.
        return _resposta(422, [_erro_de_validacao(d) for d in exc.errors()])

    @app.exception_handler(Exception)
    async def _inesperado(request: Request, exc: Exception) -> JSONResponse:
        logger.error(
            "erro_inesperado",
            extra={"tipo": type(exc).__name__, "rota": request.url.path},
        )
        return _resposta(500, [ErroCampo(None, "erro_interno", "Erro interno.")])
