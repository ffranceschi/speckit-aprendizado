"""Configuração via variáveis de ambiente. Chaves nunca são versionadas (Princípio IV)."""

import base64
import binascii
from functools import lru_cache

from pydantic import Field, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class DatabaseSettings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    database_url: str = Field(repr=False)


class Settings(DatabaseSettings):
    cadastro_encryption_key: bytes = Field(repr=False)
    cadastro_hmac_key: bytes = Field(repr=False)

    @field_validator("cadastro_encryption_key", "cadastro_hmac_key", mode="before")
    @classmethod
    def _decodificar_chave(cls, valor: str | bytes) -> bytes:
        if isinstance(valor, str):
            try:
                valor = base64.b64decode(valor, validate=True)
            except binascii.Error as exc:
                raise ValueError("a chave deve estar em base64") from exc
        if len(valor) != 32:
            raise ValueError("a chave deve ter 32 bytes")
        return valor


@lru_cache
def get_settings() -> Settings:
    return Settings()
