"""Criptografia de dados pessoais em repouso (R5): AES-256-GCM + HMAC-SHA256."""

import hashlib
import hmac
import os

from cryptography.hazmat.primitives.ciphers.aead import AESGCM

_TAMANHO_NONCE = 12


class ProtetorDadosAesGcm:
    def __init__(self, chave_cifra: bytes, chave_hmac: bytes):
        if len(chave_cifra) != 32 or len(chave_hmac) != 32:
            raise ValueError("as chaves devem ter 32 bytes")
        self._aes = AESGCM(chave_cifra)
        self._chave_hmac = chave_hmac

    def cifrar(self, valor: str) -> bytes:
        nonce = os.urandom(_TAMANHO_NONCE)
        return nonce + self._aes.encrypt(nonce, valor.encode("utf-8"), None)

    def decifrar(self, dados: bytes) -> str:
        nonce, cifrado = dados[:_TAMANHO_NONCE], dados[_TAMANHO_NONCE:]
        return self._aes.decrypt(nonce, cifrado, None).decode("utf-8")

    def hash_documento(self, documento: str) -> bytes:
        return hmac.new(self._chave_hmac, documento.encode("utf-8"), hashlib.sha256).digest()

    def __repr__(self) -> str:
        return "ProtetorDadosAesGcm(***)"
