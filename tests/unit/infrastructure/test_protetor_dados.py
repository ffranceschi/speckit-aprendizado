import base64
import os

import pytest
from pydantic import ValidationError

from cadastro_cliente.infrastructure.config import Settings
from cadastro_cliente.infrastructure.seguranca.protetor_dados import ProtetorDadosAesGcm


def _chave() -> bytes:
    return os.urandom(32)


def test_cifrar_decifrar_ida_e_volta():
    p = ProtetorDadosAesGcm(_chave(), _chave())
    assert p.decifrar(p.cifrar("52998224725")) == "52998224725"


def test_nonce_aleatorio():
    p = ProtetorDadosAesGcm(_chave(), _chave())
    a, b = p.cifrar("valor"), p.cifrar("valor")
    assert a != b
    assert b"valor" not in a


def test_adulteracao_detectada():
    p = ProtetorDadosAesGcm(_chave(), _chave())
    cifrado = bytearray(p.cifrar("valor"))
    cifrado[-1] ^= 1
    with pytest.raises(Exception):  # noqa: B017
        p.decifrar(bytes(cifrado))


def test_hash_documento_deterministico_e_com_chave():
    enc, hmac1 = _chave(), _chave()
    p1, p2 = ProtetorDadosAesGcm(enc, hmac1), ProtetorDadosAesGcm(enc, _chave())
    h = p1.hash_documento("52998224725")
    assert h == p1.hash_documento("52998224725")
    assert len(h) == 32
    assert h != p2.hash_documento("52998224725")


def test_chave_com_tamanho_errado_rejeitada():
    with pytest.raises(ValueError):
        ProtetorDadosAesGcm(b"curta", _chave())


def _b64(n: int) -> str:
    return base64.b64encode(os.urandom(n)).decode()


def test_settings_exige_chaves(monkeypatch):
    monkeypatch.setenv("DATABASE_URL", "postgresql+psycopg://x/y")
    monkeypatch.delenv("CADASTRO_ENCRYPTION_KEY", raising=False)
    monkeypatch.delenv("CADASTRO_HMAC_KEY", raising=False)
    with pytest.raises(ValidationError):
        Settings(_env_file=None)


def test_settings_valida_tamanho_e_esconde_chaves(monkeypatch):
    monkeypatch.setenv("DATABASE_URL", "postgresql+psycopg://x/y")
    monkeypatch.setenv("CADASTRO_ENCRYPTION_KEY", _b64(16))
    monkeypatch.setenv("CADASTRO_HMAC_KEY", _b64(32))
    with pytest.raises(ValidationError):
        Settings(_env_file=None)
    chave = _b64(32)
    monkeypatch.setenv("CADASTRO_ENCRYPTION_KEY", chave)
    s = Settings(_env_file=None)
    assert len(s.cadastro_encryption_key) == 32
    assert chave not in repr(s)
