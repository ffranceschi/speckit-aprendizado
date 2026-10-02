"""Endpoints REST de clientes (contracts/openapi.yaml)."""

from uuid import UUID

from fastapi import APIRouter, Response, status

from cadastro_cliente.application.casos_de_uso.criar_cliente import CriarCliente
from cadastro_cliente.application.casos_de_uso.editar_cliente import EditarCliente
from cadastro_cliente.application.casos_de_uso.listar_clientes import ListarClientes
from cadastro_cliente.application.casos_de_uso.obter_cliente import ObterCliente
from cadastro_cliente.application.casos_de_uso.remover_cliente import RemoverCliente
from cadastro_cliente.interfaces.api.dependencias import Repositorio
from cadastro_cliente.interfaces.api.schemas import (
    ClienteDetalhe,
    ClienteEntrada,
    Erros,
    PaginaClientes,
)

router = APIRouter(prefix="/clientes", tags=["clientes"])

_ERROS = {
    404: {"model": Erros, "description": "Cliente não encontrado"},
    409: {"model": Erros, "description": "Documento já cadastrado"},
    422: {"model": Erros, "description": "Dados inválidos"},
}


@router.post(
    "",
    status_code=status.HTTP_201_CREATED,
    response_model=ClienteDetalhe,
    responses={k: _ERROS[k] for k in (409, 422)},
    summary="Cadastrar cliente",
)
def criar_cliente(entrada: ClienteEntrada, repositorio: Repositorio, response: Response):
    cliente = CriarCliente(repositorio).executar(entrada.para_dados())
    response.headers["Location"] = f"/clientes/{cliente.id}"
    return ClienteDetalhe.de_cliente(cliente)


@router.get(
    "",
    response_model=PaginaClientes,
    responses={422: _ERROS[422]},
    summary="Listar clientes (paginado, 20 por página, ordenado por nome)",
)
def listar_clientes(repositorio: Repositorio, page: int = 1):
    return PaginaClientes.de_pagina(ListarClientes(repositorio).executar(page))


@router.get(
    "/{id}",
    response_model=ClienteDetalhe,
    responses={404: _ERROS[404]},
    summary="Consultar cliente",
)
def obter_cliente(id: UUID, repositorio: Repositorio):
    return ClienteDetalhe.de_cliente(ObterCliente(repositorio).executar(id))


@router.put(
    "/{id}",
    response_model=ClienteDetalhe,
    responses=_ERROS,
    summary="Editar cliente (substituição completa, mesmas validações do cadastro)",
)
def editar_cliente(id: UUID, entrada: ClienteEntrada, repositorio: Repositorio):
    return ClienteDetalhe.de_cliente(EditarCliente(repositorio).executar(id, entrada.para_dados()))


@router.delete(
    "/{id}",
    status_code=status.HTTP_204_NO_CONTENT,
    response_class=Response,
    responses={404: _ERROS[404]},
    summary="Remover cliente definitivamente",
    description="Exclusão física. A confirmação explícita (FR-015) é feita pelo cliente da API.",
)
def remover_cliente(id: UUID, repositorio: Repositorio):
    RemoverCliente(repositorio).executar(id)
    return Response(status_code=status.HTTP_204_NO_CONTENT)
