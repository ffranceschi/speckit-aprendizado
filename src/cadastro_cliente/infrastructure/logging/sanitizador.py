"""Logging estruturado com mascaramento de dados pessoais (R7, FR-018).

Defesa em profundidade: o código da aplicação loga apenas identificadores (cliente_id); este
filtro mascara CPF, CNPJ, e-mail e telefone caso algum escape. Nomes e endereços não têm padrão
reconhecível e por isso NUNCA devem ser passados ao logger.
"""

import json
import logging
import re
import sys

_LIMITE = r"(?<![\w-])"
_FIM = r"(?![\w-])"
_PADROES = [
    (re.compile(_LIMITE + r"\d{2}\.\d{3}\.\d{3}/\d{4}-\d{2}" + _FIM), "[CNPJ]"),
    (re.compile(_LIMITE + r"\d{3}\.\d{3}\.\d{3}-\d{2}" + _FIM), "[CPF]"),
    (re.compile(r"[^\s@=:,;\"'<>()\[\]]+@[^\s@]+\.[^\s@,;\"'<>()\[\]]+"), "[EMAIL]"),
    (re.compile(_LIMITE + r"\d{14}" + _FIM), "[CNPJ]"),
    (re.compile(_LIMITE + r"\d{11}" + _FIM), "[DOC/TEL]"),
    (re.compile(r"(?<![\w-])\(?\d{2}\)?[\s-]?\d{4,5}-?\d{4}" + _FIM), "[TELEFONE]"),
]

_ATRIBUTOS_PADRAO = set(vars(logging.LogRecord("", 0, "", 0, "", None, None))) | {
    "message",
    "asctime",
    "taskName",
}


def mascarar(texto: str) -> str:
    for padrao, substituto in _PADROES:
        texto = padrao.sub(substituto, texto)
    return texto


def _mascarar_valor(valor):
    return mascarar(valor) if isinstance(valor, str) else valor


class FiltroDadosSensiveis(logging.Filter):
    def filter(self, record: logging.LogRecord) -> bool:
        # Mascara msg e args separadamente, preservando a estrutura de args: formatters como o
        # de acesso do uvicorn dependem dela.
        if isinstance(record.msg, str):
            record.msg = mascarar(record.msg)
        if isinstance(record.args, tuple):
            record.args = tuple(_mascarar_valor(a) for a in record.args)
        elif isinstance(record.args, dict):
            record.args = {k: _mascarar_valor(v) for k, v in record.args.items()}
        for chave, valor in list(vars(record).items()):
            if chave not in _ATRIBUTOS_PADRAO and isinstance(valor, str):
                setattr(record, chave, mascarar(valor))
        if record.exc_info and not record.exc_text:
            record.exc_text = mascarar(logging.Formatter().formatException(record.exc_info))
        elif record.exc_text:
            record.exc_text = mascarar(record.exc_text)
        return True


class FormatadorJson(logging.Formatter):
    def format(self, record: logging.LogRecord) -> str:
        dados = {
            "ts": self.formatTime(record, "%Y-%m-%dT%H:%M:%S%z"),
            "level": record.levelname,
            "logger": record.name,
            "msg": record.getMessage(),
        }
        dados.update({k: v for k, v in vars(record).items() if k not in _ATRIBUTOS_PADRAO})
        if record.exc_text:
            dados["exc"] = record.exc_text
        return json.dumps(dados, ensure_ascii=False, default=str)


def configurar_logging(nivel: int = logging.INFO) -> None:
    """Idempotente: instala handler JSON com filtro no root e filtro nos loggers do uvicorn."""
    root = logging.getLogger()
    if not any(getattr(h, "_cadastro_cliente", False) for h in root.handlers):
        handler = logging.StreamHandler(sys.stdout)
        handler.setFormatter(FormatadorJson())
        handler.addFilter(FiltroDadosSensiveis())
        handler._cadastro_cliente = True  # type: ignore[attr-defined]
        root.addHandler(handler)
    root.setLevel(nivel)
    for nome in ("uvicorn", "uvicorn.access", "uvicorn.error"):
        logger = logging.getLogger(nome)
        if not any(isinstance(f, FiltroDadosSensiveis) for f in logger.filters):
            logger.addFilter(FiltroDadosSensiveis())
