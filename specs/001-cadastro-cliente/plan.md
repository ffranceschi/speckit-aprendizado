# Implementation Plan: Cadastro de Cliente

**Branch**: `001-cadastro-cliente` | **Date**: 2026-10-02 | **Spec**: [spec.md](./spec.md)

**Input**: Feature specification from `/specs/001-cadastro-cliente/spec.md`

**Note**: This template is filled in by the `/speckit-plan` command; its definition describes the execution workflow.

## Summary

API REST de cadastro de cliente (criar, listar paginado, consultar, editar, remover) com
documento único (CPF ou CNPJ em campo único), validação de e-mail, telefone e endereço completo.
Abordagem: Clean Architecture em Python/FastAPI; regras de negócio em value objects de domínio
puros; PostgreSQL via SQLAlchemy com dados pessoais cifrados (AES-256-GCM) e unicidade por HMAC
do documento; logging com sanitização de dados pessoais; testes pytest em três níveis (unitário,
integração, contrato). Detalhes em [research.md](./research.md).

## Technical Context

**Language/Version**: Python 3.12

**Primary Dependencies**: FastAPI, Uvicorn, Pydantic v2, pydantic-settings, SQLAlchemy 2.x,
psycopg 3, Alembic, cryptography

**Storage**: PostgreSQL 16 (volume com criptografia de disco no ambiente de produção)

**Testing**: pytest, httpx/`TestClient` (FastAPI), testcontainers[postgres]

**Target Platform**: Linux server (container Docker); desenvolvimento em macOS/Linux

**Project Type**: web-service (somente backend; interface de usuário fora do escopo)

**Performance Goals**: primeira página da listagem em ≤ 2 s com 10.000 clientes (SC-004); demais
operações percebidas como instantâneas pelo operador (< 500 ms p95 local)

**Constraints**: nenhum dado pessoal em texto claro em logs/erros; chaves somente via ambiente;
domínio sem dependência de framework

**Scale/Scope**: até 10.000 clientes; poucos operadores internos simultâneos; 5 endpoints

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

| Princípio / Regra | Como o plano atende | Pré-design | Pós-design |
|-------------------|---------------------|:----------:|:----------:|
| I. Clean Architecture | Camadas `domain` → `application` → `interfaces/api` / `infrastructure`; domínio sem FastAPI/SQLAlchemy/Pydantic; repositório e criptografia atrás de portas (R2, data-model "Portas") | ✅ | ✅ |
| I. Regra fora de controller/ORM/migration | Validações em value objects; schemas Pydantic só validam forma (R3) | ✅ | ✅ |
| II. Testes de regras de negócio (NÃO NEGOCIÁVEL) | Unit tests de domínio e casos de uso sem banco; integração com PostgreSQL real; contrato HTTP (R11) | ✅ | ✅ |
| III. CPF/CNPJ validado no domínio | `Documento` value object: normalização, tamanho, dígitos iguais, DV módulo 11 (R4) | ✅ | ✅ |
| III. Normalização antes de unicidade/armazenamento | Somente dígitos → HMAC → `UNIQUE` (R5, R6) | ✅ | ✅ |
| IV. Sem dado pessoal em logs/erros | Filtro sanitizador no logging; handler 422 sem `input`; mensagens sem valores; `repr` mascarado (R7, R12) | ✅ | ✅ |
| IV. Criptografia em repouso + HMAC para unicidade | AES-256-GCM em documento/e-mail/telefone/endereço; `documento_hash` HMAC-SHA256 (R5) | ⚠️ `nome` | ⚠️ justificado |
| IV. Segredos fora do repositório | Chaves via env/pydantic-settings; `.env` no `.gitignore` (R5, quickstart) | ✅ | ✅ |
| IV. TLS | Terminação TLS no proxy/ingress do ambiente; fora do código da aplicação | ✅ | ✅ |
| IV. Dados de teste fictícios | Gerador de CPF/CNPJ válidos nos testes (R11) | ✅ | ✅ |
| Seg. & Privacidade: coletar só o necessário (LGPD) | Apenas campos da spec; exclusão definitiva (R9) | ✅ | ✅ |
| Fluxo: tarefas de teste e de proteção | A ser garantido em `/speckit-tasks` (estrutura de testes definida aqui) | ✅ | ✅ |
| Simplicidade (YAGNI) | Sem cache, sem async, sem soft delete, sem controle otimista | ✅ | ✅ |

**Resultado**: GATE aprovado. Única ressalva (⚠️) é `nome` em texto no banco, justificada em
Complexity Tracking.

## Project Structure

### Documentation (this feature)

```text
specs/001-cadastro-cliente/
├── plan.md              # This file (/speckit-plan command output)
├── research.md          # Phase 0 output (/speckit-plan command)
├── data-model.md        # Phase 1 output (/speckit-plan command)
├── quickstart.md        # Phase 1 output (/speckit-plan command)
├── contracts/
│   └── openapi.yaml     # Phase 1 output (/speckit-plan command)
└── tasks.md             # Phase 2 output (/speckit-tasks command - NOT created by /speckit-plan)
```

### Source Code (repository root)

```text
pyproject.toml
alembic.ini
docker-compose.yml               # serviço db (PostgreSQL 16)
.env.example                     # nomes das variáveis, sem valores reais

src/cadastro_cliente/
├── domain/
│   ├── cliente.py               # entidade Cliente, TipoPessoa
│   ├── documento.py             # value object Documento (CPF/CNPJ)
│   ├── contato.py               # value objects Email, Telefone
│   ├── endereco.py              # value object Endereco, UFs
│   └── erros.py                 # ErroCampo, DadosInvalidosError, DocumentoDuplicadoError, ClienteNaoEncontradoError
├── application/
│   ├── portas.py                # ClienteRepository, ProtetorDados, Pagina
│   ├── dto.py                   # dados de entrada/saída dos casos de uso
│   └── casos_de_uso/
│       ├── criar_cliente.py
│       ├── listar_clientes.py
│       ├── obter_cliente.py
│       ├── editar_cliente.py
│       └── remover_cliente.py
├── interfaces/api/
│   ├── rotas_clientes.py        # endpoints FastAPI
│   ├── schemas.py               # modelos Pydantic de request/response
│   ├── erros.py                 # exception handlers (sem eco de input)
│   └── dependencias.py          # injeção de casos de uso/sessão
├── infrastructure/
│   ├── config.py                # Settings (pydantic-settings)
│   ├── db/
│   │   ├── modelos.py           # ClienteModel (SQLAlchemy)
│   │   ├── sessao.py
│   │   └── repositorio_cliente.py
│   ├── seguranca/
│   │   └── protetor_dados.py    # AES-256-GCM + HMAC-SHA256
│   └── logging/
│       └── sanitizador.py       # logging.Filter que mascara dados pessoais
└── main.py                      # composição da aplicação FastAPI

migrations/                      # Alembic
└── versions/

tests/
├── conftest.py
├── fabricas.py                  # gerador de CPF/CNPJ fictícios e payloads
├── unit/
│   ├── domain/
│   └── application/             # com repositório em memória
├── integration/                 # repositório + criptografia contra PostgreSQL (testcontainers)
└── contract/                    # endpoints vs contracts/openapi.yaml + checagem de logs
```

**Structure Decision**: projeto único (somente backend) com layout `src/`, organizado pelas camadas
da Clean Architecture exigidas pelo Princípio I. Os testes espelham os níveis definidos em R11.

## Complexity Tracking

> **Fill ONLY if Constitution Check has violations that must be justified**

| Violation | Why Needed | Simpler Alternative Rejected Because |
|-----------|------------|-------------------------------------|
| `nome` armazenado sem criptografia de aplicação (Princípio IV pede criptografia em repouso para dados pessoais) | FR-011 exige listagem paginada ordenada por nome com totais; o banco precisa ordenar pelo valor | Cifrar `nome` obrigaria carregar e decifrar todos os registros para ordenar em memória a cada página (inviável para SC-004 e cresce com a base). Mitigação: criptografia de disco/volume do PostgreSQL, `nome` nunca logado, demais dados pessoais cifrados na aplicação |
