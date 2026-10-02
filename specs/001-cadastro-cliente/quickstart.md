# Quickstart: Cadastro de Cliente

Guia para subir o módulo e validar a feature de ponta a ponta. Detalhes de payloads em
[contracts/openapi.yaml](./contracts/openapi.yaml); regras de campos em
[data-model.md](./data-model.md).

## Pré-requisitos

- Python 3.12 e [`uv`](https://docs.astral.sh/uv/)
- Docker (PostgreSQL local e testes de integração)

## Setup

```bash
uv sync                                   # instala dependências do pyproject.toml
docker compose up -d db                   # PostgreSQL 16 em localhost:5432
# Porta 5432 ocupada? Use DB_PORT=55432 docker compose up -d db e ajuste DATABASE_URL no .env

cp .env.example .env                      # depois gere as chaves:
python -c "import os,base64;print(base64.b64encode(os.urandom(32)).decode())"  # CADASTRO_ENCRYPTION_KEY
python -c "import os,base64;print(base64.b64encode(os.urandom(32)).decode())"  # CADASTRO_HMAC_KEY

uv run alembic upgrade head               # cria a tabela clientes
uv run uvicorn cadastro_cliente.main:app --reload
```

`.env` nunca é versionado (apenas `.env.example`, sem valores reais). Sem as chaves, a aplicação
não inicia.

## Testes

```bash
uv run pytest tests/unit          # domínio + casos de uso, sem banco (rápido)
uv run pytest tests/integration   # PostgreSQL via testcontainers (requer Docker)
uv run pytest tests/contract      # endpoints HTTP vs contrato + verificação de logs
uv run pytest                     # tudo
```

Resultado esperado: todos os testes passando.

## Cenários de validação manual

Use documentos fictícios. Exemplos válidos: CPF `529.982.247-25`, CNPJ `11.222.333/0001-81`.

| # | Ação | Resultado esperado | Ref. |
|---|------|--------------------|------|
| 1 | `POST /clientes` com CPF `529.982.247-25` e dados válidos | `201`, `tipo_pessoa: FISICA`, header `Location` | US1-1 |
| 2 | `POST /clientes` com CNPJ `11.222.333/0001-81` | `201`, `tipo_pessoa: JURIDICA` | US1-2 |
| 3 | Repetir o passo 1 com documento `52998224725` | `409`, `code: documento_duplicado`, sem o número na resposta | US1-3, SC-002 |
| 4 | `POST` com documento `529.982.247-26` e e-mail `joao@` | `422` listando **os dois** erros | US1-4/5, FR-010 |
| 5 | `POST` com documento `111.111.111-11` | `422`, `documento_invalido` | Edge case |
| 6 | `POST` sem `endereco.cep` e com `nome: "   "` | `422` com `endereco.cep` e `nome` = `obrigatorio` | US1-6, FR-009 |
| 7 | `GET /clientes` | `200`, ordenado por nome, `page_size: 20`, `documento_mascarado` | US2-1, FR-011/012 |
| 8 | `GET /clientes?page=99` | `200`, `items: []`, totais corretos | FR-011 |
| 9 | `GET /clientes/{id}` do passo 1 | `200`, documento completo formatado | US2-4 |
| 10 | `PUT /clientes/{id}` (passo 1) com o CNPJ do passo 2 | `409`; `GET` mostra dados originais | US3-2 |
| 11 | `PUT /clientes/{id}` com novo e-mail válido | `200`, novo e-mail | US3-1 |
| 12 | `DELETE /clientes/{id}` (passo 1) | `204`; `GET` → `404` | US4-1 |
| 13 | Repetir o passo 1 | `201` (documento liberado) | US4-3 |
| 14 | `DELETE` / `PUT` em UUID inexistente | `404`, `cliente_nao_encontrado` | US3-4, US4-4 |

## Verificação de privacidade

- Após os cenários, busque nos logs da aplicação: nenhum CPF, CNPJ, e-mail ou telefone completo
  deve aparecer (SC-005). Ex.: `grep -E '52998224725|529\.982\.247-25|@example\.com' app.log`
  não retorna nada.
- No banco: `SELECT nome, documento_cifrado, documento_hash FROM clientes;` — documento, e-mail,
  telefone e endereço aparecem apenas como bytes cifrados.
