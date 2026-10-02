"""Repositório SQL de clientes: cifra dados pessoais e garante unicidade por HMAC (R5, R6)."""

import json
from uuid import UUID

from sqlalchemy import delete, func, select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from cadastro_cliente.application.portas import Pagina, ProtetorDados
from cadastro_cliente.domain.cliente import Cliente
from cadastro_cliente.domain.contato import Email, Telefone
from cadastro_cliente.domain.documento import Documento
from cadastro_cliente.domain.endereco import Endereco
from cadastro_cliente.domain.erros import ClienteNaoEncontradoError, DocumentoDuplicadoError
from cadastro_cliente.infrastructure.db.modelos import ClienteModel

_CONSTRAINT_DOCUMENTO = "uq_clientes_documento_hash"


def _violou_unicidade_documento(exc: IntegrityError) -> bool:
    diag = getattr(exc.orig, "diag", None)
    return getattr(diag, "constraint_name", None) == _CONSTRAINT_DOCUMENTO


class RepositorioClienteSQL:
    def __init__(self, sessao: Session, protetor: ProtetorDados):
        self._sessao = sessao
        self._protetor = protetor

    def _preencher_modelo(self, modelo: ClienteModel, cliente: Cliente) -> None:
        p = self._protetor
        modelo.nome = cliente.nome
        modelo.tipo_pessoa = cliente.tipo_pessoa.value
        modelo.documento_hash = p.hash_documento(cliente.documento.valor)
        modelo.documento_cifrado = p.cifrar(cliente.documento.valor)
        modelo.email_cifrado = p.cifrar(cliente.email.valor)
        modelo.telefone_cifrado = p.cifrar(cliente.telefone.valor)
        modelo.endereco_cifrado = p.cifrar(json.dumps(cliente.endereco.para_dict()))
        modelo.criado_em = cliente.criado_em
        modelo.atualizado_em = cliente.atualizado_em

    def _para_modelo(self, cliente: Cliente) -> ClienteModel:
        modelo = ClienteModel(id=cliente.id)
        self._preencher_modelo(modelo, cliente)
        return modelo

    def _para_entidade(self, modelo: ClienteModel) -> Cliente:
        p = self._protetor
        return Cliente(
            id=modelo.id,
            nome=modelo.nome,
            documento=Documento(p.decifrar(modelo.documento_cifrado)),
            email=Email(p.decifrar(modelo.email_cifrado)),
            telefone=Telefone(p.decifrar(modelo.telefone_cifrado)),
            endereco=Endereco.criar(**json.loads(p.decifrar(modelo.endereco_cifrado))),
            criado_em=modelo.criado_em,
            atualizado_em=modelo.atualizado_em,
        )

    def _gravar(self, operacao) -> None:
        """Executa a escrita num savepoint e traduz violação de unicidade para erro de domínio."""
        try:
            with self._sessao.begin_nested():
                operacao()
                self._sessao.flush()
        except IntegrityError as exc:
            if _violou_unicidade_documento(exc):
                raise DocumentoDuplicadoError() from None
            raise

    def adicionar(self, cliente: Cliente) -> None:
        self._gravar(lambda: self._sessao.add(self._para_modelo(cliente)))

    def existe_documento(self, documento: Documento, ignorar_id: UUID | None = None) -> bool:
        consulta = select(ClienteModel.id).where(
            ClienteModel.documento_hash == self._protetor.hash_documento(documento.valor)
        )
        if ignorar_id is not None:
            consulta = consulta.where(ClienteModel.id != ignorar_id)
        return self._sessao.execute(consulta.limit(1)).first() is not None

    def obter(self, id_: UUID) -> Cliente | None:
        modelo = self._sessao.get(ClienteModel, id_)
        return self._para_entidade(modelo) if modelo else None

    def listar(self, pagina: int, tamanho: int) -> Pagina[Cliente]:
        total = self._sessao.scalar(select(func.count()).select_from(ClienteModel)) or 0
        modelos = self._sessao.scalars(
            select(ClienteModel)
            .order_by(ClienteModel.nome, ClienteModel.id)
            .limit(tamanho)
            .offset((pagina - 1) * tamanho)
        )
        return Pagina(
            itens=[self._para_entidade(m) for m in modelos],
            pagina=pagina,
            tamanho=tamanho,
            total_itens=total,
        )

    def atualizar(self, cliente: Cliente) -> None:
        modelo = self._sessao.get(ClienteModel, cliente.id)
        if modelo is None:
            raise ClienteNaoEncontradoError()
        try:
            self._gravar(lambda: self._preencher_modelo(modelo, cliente))
        except DocumentoDuplicadoError:
            self._sessao.refresh(modelo)  # descarta valores rejeitados pelo banco
            raise

    def remover(self, id_: UUID) -> bool:
        resultado = self._sessao.execute(delete(ClienteModel).where(ClienteModel.id == id_))
        return resultado.rowcount > 0
