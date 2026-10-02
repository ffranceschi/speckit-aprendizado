---

description: "Task list for feature 001-cadastro-cliente"
---

# Tasks: Cadastro de Cliente

**Input**: Design documents from `/specs/001-cadastro-cliente/`

**Prerequisites**: plan.md, spec.md, research.md, data-model.md, contracts/openapi.yaml, quickstart.md

**Tests**: OBRIGATÓRIOS. Pedidos pelo usuário ("Escrever testes de cada endpoint") e exigidos pela
constituição (Princípio II — testes para toda regra de negócio). Abordagem test-first: cada teste
MUST ser escrito e falhar antes da implementação correspondente.

**Organization**: Tasks are grouped by user story to enable independent implementation and testing of each story.

## Format: `[ID] [P?] [Story] Description`

- **[P]**: Can run in parallel (different files, no dependencies)
- **[Story]**: Which user story this task belongs to (US1–US4)
- Pacote Python: `src/cadastro_cliente/` (abreviado abaixo como `src/cadastro_cliente/...`)

## Mapeamento do pedido do usuário

| Pedido | Tarefas |
|--------|---------|
| Criar model Cliente | T019 (entidade de domínio), T026 (modelo SQLAlchemy) |
| Criar migration | T027 |
| Implementar validação de CPF/CNPJ único | T009/T016 (validação), T036/T038/T039 (unicidade no cadastro), T052/T055/T056 (unicidade na edição) |
| Criar endpoints REST | T040 (POST), T051 (GETs), T057 (PUT), T063 (DELETE) |
| Escrever testes de cada endpoint | T037 (POST), T045/T046 (GETs), T054 (PUT), T060 (DELETE), T064/T065 |

---

## Phase 1: Setup (Shared Infrastructure)

**Purpose**: Project initialization and basic structure

- [X] T001 Criar `pyproject.toml` (projeto `cadastro-cliente`, Python `>=3.12`, layout `src/`) com dependências `fastapi`, `uvicorn[standard]`, `pydantic>=2`, `pydantic-settings`, `sqlalchemy>=2`, `psycopg[binary]>=3`, `alembic`, `cryptography` e grupo dev `pytest`, `httpx`, `testcontainers[postgres]`, `pyyaml`, `ruff`; rodar `uv sync` para gerar `uv.lock`
- [X] T002 Criar a árvore de pacotes do plan.md com `__init__.py` vazios: `src/cadastro_cliente/{domain,application,application/casos_de_uso,interfaces,interfaces/api,infrastructure,infrastructure/db,infrastructure/seguranca,infrastructure/logging}/` e `tests/{unit/domain,unit/application,unit/infrastructure,integration,contract}/`
- [X] T003 [P] Criar `docker-compose.yml` com serviço `db` (`postgres:16`, porta 5432, banco/usuário/senha `cadastro` só para desenvolvimento local, volume nomeado)
- [X] T004 [P] Criar `.env.example` com as variáveis `DATABASE_URL`, `CADASTRO_ENCRYPTION_KEY`, `CADASTRO_HMAC_KEY` (valores de exemplo vazios/comentados) e `.gitignore` incluindo `.env`, `.venv/`, `__pycache__/`, `.pytest_cache/`, `.ruff_cache/`, `.DS_Store`, `.idea/`
- [X] T005 [P] Configurar Ruff (lint + format, `line-length = 100`, regras `E,F,I,B,UP`) e pytest (`testpaths = ["tests"]`, `pythonpath = ["src"]`, marcador `integration`) em `pyproject.toml`
- [X] T006 Inicializar Alembic: `alembic.ini` e `migrations/env.py` lendo `DATABASE_URL` de `cadastro_cliente.infrastructure.config` e usando `Base.metadata` de `cadastro_cliente.infrastructure.db.modelos`

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: Domínio, portas, criptografia, persistência e esqueleto da API usados por todas as stories

**⚠️ CRITICAL**: No user story work can begin until this phase is complete

### Testes do domínio e da infraestrutura base (escrever primeiro, devem falhar)

- [X] T007 [P] Criar `tests/fabricas.py` com `gerar_cpf()` e `gerar_cnpj()` (documentos fictícios válidos calculando DV módulo 11), `payload_cliente(**sobrescritas)` (dict completo conforme `ClienteEntrada` de contracts/openapi.yaml) e constantes de exemplo `CPF_VALIDO = "529.982.247-25"`, `CNPJ_VALIDO = "11.222.333/0001-81"`
- [X] T008 [P] Criar `tests/unit/domain/test_erros.py` validando que `DadosInvalidosError` carrega lista de `ErroCampo(field, code, message)` e que nenhuma mensagem contém o valor informado
- [X] T009 [P] Criar `tests/unit/domain/test_documento.py`: aceita `529.982.247-25` e `52998224725` como o mesmo documento (igualdade e `valor == "52998224725"`); 11 dígitos → `FISICA`, 14 → `JURIDICA`; rejeita com `documento_invalido`: tamanho ≠ 11/14, todos os dígitos iguais (`000.000.000-00`, `111.111.111-11`, `00000000000000`), DV incorreto (`529.982.247-26`), letras; `formatado()` → `529.982.247-25` / `11.222.333/0001-81`; `mascarado()` → `***.982.247-**` / `**.222.333/0001-**`; `repr()`/`str()` retornam a forma mascarada
- [X] T010 [P] Criar `tests/unit/domain/test_contato.py`: `Email` — "`strip()`; obrigatório; máx. 254 caracteres; normalizado para minúsculas", formato "exatamente um `@`, parte local não vazia sem espaços, domínio com ao menos um ponto, rótulos não vazios" (rejeitar `joao@`, `joao`, `jo ao@x.com`, `a@@b.com`, `a@b`, `a@.com`; aceitar `  Maria@Example.com ` → `maria@example.com`); `Telefone` — "10 ou 11 dígitos; DDD (2 primeiros dígitos) entre 11 e 99 sem zero na primeira posição", `formatado()` → `(11) 98765-4321` / `(11) 3456-7890`, erros `telefone_invalido`
- [X] T011 [P] Criar `tests/unit/domain/test_endereco.py`: obrigatórios `logradouro` (1–200), `numero` (1–20, aceita "S/N"), `bairro` (1–100), `cidade` (1–100), `uf` (uma das 27 siglas, normalizada para maiúsculas), `cep` (8 dígitos após remover pontuação); `complemento` opcional 0–100, vazio → `None`; erros com `field` `endereco.<subcampo>` e códigos `obrigatorio`, `tamanho_invalido`, `uf_invalida`, `cep_invalido`; todos os erros reportados juntos
- [X] T012 [P] Criar `tests/unit/domain/test_cliente.py`: `Cliente.criar(...)` com dados válidos gera `id` uuid4, `tipo_pessoa` derivado do documento, `criado_em == atualizado_em` (UTC); `nome` "Obrigatório; `strip()`; 2–150 caracteres; só espaços = vazio"; dados inválidos em vários campos geram **um** `DadosInvalidosError` com **todos** os erros (FR-010); `Cliente.atualizar(...)` revalida tudo, preserva `id`/`criado_em` e altera `atualizado_em`
- [X] T013 [P] Criar `tests/unit/infrastructure/test_protetor_dados.py`: `cifrar`/`decifrar` ida e volta; dois `cifrar` do mesmo valor geram bytes diferentes (nonce aleatório); bytes adulterados → erro; `hash_documento` determinístico, 32 bytes, muda com outra chave HMAC; `Settings` falha sem `CADASTRO_ENCRYPTION_KEY`/`CADASTRO_HMAC_KEY` ou com chave ≠ 32 bytes
- [X] T014 [P] Criar `tests/unit/infrastructure/test_sanitizador.py`: o filtro mascara em `msg` e `args` CPF (com/sem pontuação), CNPJ (com/sem pontuação), e-mail e telefone; não altera UUIDs nem texto sem dados pessoais

### Domínio

- [X] T015 [P] Implementar `src/cadastro_cliente/domain/erros.py`: `ErroCampo` (dataclass `field: str | None`, `code`, `message`), `DadosInvalidosError(erros: list[ErroCampo])`, `DocumentoDuplicadoError`, `ClienteNaoEncontradoError` — mensagens em pt-BR sem valores informados (faz T008 passar)
- [X] T016 [P] Implementar `src/cadastro_cliente/domain/documento.py`: `TipoPessoa` (enum `FISICA`, `JURIDICA`) e value object imutável `Documento` com normalização, validação de tamanho, dígitos iguais e DV módulo 11 (CPF pesos 10..2 / 11..2; CNPJ 5..2,9..2 / 6..2,9..2), `formatado()`, `mascarado()`, `__repr__`/`__str__` mascarados (faz T009 passar)
- [X] T017 [P] Implementar `src/cadastro_cliente/domain/contato.py`: value objects `Email` e `Telefone` conforme T010 (faz T010 passar)
- [X] T018 [P] Implementar `src/cadastro_cliente/domain/endereco.py`: constante `UFS` com as 27 siglas e value object `Endereco` conforme T011, com construtor que acumula todos os erros de subcampos (faz T011 passar)
- [X] T019 Implementar `src/cadastro_cliente/domain/cliente.py`: entidade `Cliente` com `criar(...)` e `atualizar(...)` que constroem todos os value objects acumulando erros e lançam um único `DadosInvalidosError` (faz T012 passar; depende de T015–T018)

### Aplicação (portas e DTOs)

- [X] T020 Implementar `src/cadastro_cliente/application/portas.py`: `Pagina[T]` (`itens`, `pagina`, `tamanho`, `total_itens`, `total_paginas`), protocolo `ClienteRepository` (`adicionar`, `atualizar`, `obter(id) -> Cliente | None`, `remover(id) -> bool`, `existe_documento(documento, ignorar_id=None) -> bool`, `listar(pagina, tamanho) -> Pagina[Cliente]`) e protocolo `ProtetorDados` (`cifrar(str) -> bytes`, `decifrar(bytes) -> str`, `hash_documento(str) -> bytes`)
- [X] T021 [P] Implementar `src/cadastro_cliente/application/dto.py`: `DadosCliente` (entrada com strings cruas: `nome`, `documento`, `email`, `telefone`, `endereco: DadosEndereco`) e `TAMANHO_PAGINA = 20`
- [X] T022 Criar `tests/unit/application/fakes.py` com `RepositorioClienteEmMemoria` (implementa `ClienteRepository`, unicidade por `documento.valor`, ordenação por `nome, id`) para os testes de casos de uso

### Infraestrutura base

- [X] T023 Implementar `src/cadastro_cliente/infrastructure/config.py`: `Settings` (pydantic-settings, prefixo vazio, lê `.env`) com `database_url`, `cadastro_encryption_key`, `cadastro_hmac_key` (base64 decodificado e validado com 32 bytes) e `get_settings()` em cache
- [X] T024 Implementar `src/cadastro_cliente/infrastructure/seguranca/protetor_dados.py`: `ProtetorDadosAesGcm` com AES-256-GCM (`AESGCM`, nonce de 12 bytes armazenado como `nonce || ciphertext`) e `hash_documento` HMAC-SHA256 (faz T013 passar)
- [X] T025 Implementar `src/cadastro_cliente/infrastructure/logging/sanitizador.py`: `FiltroDadosSensiveis(logging.Filter)` + `configurar_logging()` com formato JSON e filtro no root logger e nos loggers `uvicorn`/`uvicorn.access`/`uvicorn.error` (faz T014 passar)
- [X] T026 Criar o model Cliente em `src/cadastro_cliente/infrastructure/db/modelos.py`: `Base` (DeclarativeBase) e `ClienteModel` (tabela `clientes`) com colunas `id uuid PK`, `nome varchar(150) NOT NULL`, `tipo_pessoa varchar(8) NOT NULL CHECK in ('FISICA','JURIDICA')`, `documento_hash bytea NOT NULL UNIQUE`, `documento_cifrado bytea NOT NULL`, `email_cifrado bytea NOT NULL`, `telefone_cifrado bytea NOT NULL`, `endereco_cifrado bytea NOT NULL`, `criado_em timestamptz NOT NULL`, `atualizado_em timestamptz NOT NULL`, índice `ix_clientes_nome (nome, id)`
- [X] T027 Criar migration `migrations/versions/0001_criar_tabela_clientes.py` (Alembic) que cria a tabela `clientes`, a constraint `uq_clientes_documento_hash`, o check de `tipo_pessoa` e o índice `ix_clientes_nome (nome, id)`, com `downgrade` que remove a tabela
- [X] T028 Implementar `src/cadastro_cliente/infrastructure/db/sessao.py`: `criar_engine(settings)`, `SessionLocal` e dependência geradora `obter_sessao()` com commit/rollback
- [X] T029 Implementar a base de `src/cadastro_cliente/infrastructure/db/repositorio_cliente.py`: classe `RepositorioClienteSQL(sessao, protetor)` com métodos privados `_para_modelo(cliente)` (cifra documento/e-mail/telefone e endereço serializado em JSON; calcula `documento_hash`) e `_para_entidade(modelo)` (decifra e reconstrói value objects)

### API base e testes de infraestrutura compartilhada

- [X] T030 [P] Implementar `src/cadastro_cliente/interfaces/api/schemas.py` com `EnderecoEntrada`, `ClienteEntrada`, `Endereco`, `ClienteDetalhe`, `ErroCampo`, `Erros` conforme contracts/openapi.yaml (somente tipos/forma; sem regras de negócio — R3)
- [X] T031 Implementar `src/cadastro_cliente/interfaces/api/erros.py`: handlers para `DadosInvalidosError` → 422, `DocumentoDuplicadoError` → 409, `ClienteNaoEncontradoError` → 404 e `RequestValidationError` → 422 no formato `Erros` **sem o campo `input`** e sem valores informados (R7, R12)
- [X] T032 Implementar `src/cadastro_cliente/interfaces/api/dependencias.py`: providers FastAPI que montam `RepositorioClienteSQL` com a sessão e `ProtetorDadosAesGcm` com `get_settings()`
- [X] T033 Implementar `src/cadastro_cliente/main.py`: `criar_app()` que chama `configurar_logging()`, registra os handlers de T031 e inclui o router de `src/cadastro_cliente/interfaces/api/rotas_clientes.py` (criar arquivo com `APIRouter(prefix="/clientes")` vazio); `app = criar_app()`
- [X] T034 Criar `tests/conftest.py`: fixture de sessão `postgres` (testcontainers `PostgresContainer("postgres:16")`) que roda `alembic upgrade head`; fixture `sessao` com rollback/limpeza da tabela por teste; fixture `settings` com chaves aleatórias de 32 bytes; fixture `client` (`TestClient(criar_app())` com dependências sobrescritas para o banco de teste); fixture `logs_sem_dados_pessoais(caplog)` que, ao final do teste, falha se algum documento/e-mail/telefone usado aparecer nos registros

**Checkpoint**: `uv run pytest tests/unit` verde; `alembic upgrade head` cria a tabela — stories podem começar

---

## Phase 3: User Story 1 - Cadastrar cliente (Priority: P1) 🎯 MVP

**Goal**: Operador cadastra cliente com documento único (CPF/CNPJ), e-mail, telefone e endereço válidos.

**Independent Test**: `POST /clientes` aceita dados válidos (201) e recusa duplicados (409) e inválidos (422 com todos os erros) — quickstart cenários 1–6.

### Tests for User Story 1 ⚠️ (escrever primeiro, devem falhar)

- [X] T035 [P] [US1] Criar `tests/unit/application/test_criar_cliente.py` com o repositório em memória: cria cliente válido (CPF e CNPJ); documento já existente com outra pontuação (`52998224725` após `529.982.247-25`) → `DocumentoDuplicadoError`; dados inválidos → `DadosInvalidosError` com todos os campos; nada é gravado em caso de erro
- [X] T036 [P] [US1] Criar `tests/integration/test_repositorio_adicionar.py`: `adicionar` grava colunas `*_cifrado` sem o texto claro (verificar via SQL que `documento_cifrado` não contém `52998224725`); `existe_documento` encontra por hash; inserir duas vezes o mesmo documento em sessões diferentes → `DocumentoDuplicadoError` (constraint `UNIQUE`, R6)
- [X] T037 [P] [US1] Criar `tests/contract/test_post_clientes.py` (teste do endpoint POST): 201 com body `ClienteDetalhe` e header `Location`; `tipo_pessoa` `FISICA`/`JURIDICA`; 409 `documento_duplicado` cujo body não contém o documento; 422 com documento `529.982.247-26` + e-mail `joao@` listando os dois erros; 422 para `111.111.111-11`; 422 com `nome: "   "` e sem `endereco.cep` → `obrigatorio` em ambos; 422 de payload malformado sem campo `input` no body; usar fixture `logs_sem_dados_pessoais`

### Implementation for User Story 1

- [X] T038 [US1] Implementar `src/cadastro_cliente/application/casos_de_uso/criar_cliente.py`: `CriarCliente(repo).executar(dados: DadosCliente) -> Cliente` — constrói `Cliente.criar`, verifica `repo.existe_documento` (→ `DocumentoDuplicadoError`), chama `repo.adicionar` (faz T035 passar)
- [X] T039 [US1] Implementar em `src/cadastro_cliente/infrastructure/db/repositorio_cliente.py` os métodos `adicionar` (flush; `IntegrityError` em `uq_clientes_documento_hash` → `DocumentoDuplicadoError`) e `existe_documento(documento, ignorar_id=None)` por `documento_hash` (faz T036 passar)
- [X] T040 [US1] Implementar `POST /clientes` em `src/cadastro_cliente/interfaces/api/rotas_clientes.py`: converte `ClienteEntrada` → `DadosCliente`, executa `CriarCliente`, retorna 201 com `ClienteDetalhe` (documento formatado completo, telefone e CEP formatados) e `Location: /clientes/{id}` (faz T037 passar)
- [X] T041 [US1] Adicionar log de operação em `src/cadastro_cliente/application/casos_de_uso/criar_cliente.py` registrando apenas `cliente_id` e `tipo_pessoa` (`logger.info("cliente_criado", extra={...})`), nunca dados pessoais

**Checkpoint**: US1 funcional e testável sozinha (MVP)

---

## Phase 4: User Story 2 - Listar e consultar clientes (Priority: P2)

**Goal**: Operador vê lista paginada (20/página, ordenada por nome, com totais e documento mascarado) e consulta um cliente.

**Independent Test**: com clientes inseridos diretamente pelo repositório, `GET /clientes` e `GET /clientes/{id}` retornam os dados esperados — quickstart cenários 7–9.

### Tests for User Story 2 ⚠️ (escrever primeiro, devem falhar)

- [X] T042 [P] [US2] Criar `tests/unit/application/test_listar_clientes.py`: 45 clientes → página 1 com 20, página 3 com 5, `total_itens=45`, `total_paginas=3`; ordenação por nome; página 99 → `itens=[]` com totais corretos; 0 clientes → `total_paginas=0`; `pagina < 1` → `DadosInvalidosError` (`field="page"`)
- [X] T043 [P] [US2] Criar `tests/unit/application/test_obter_cliente.py`: retorna cliente existente; id inexistente → `ClienteNaoEncontradoError`
- [X] T044 [P] [US2] Criar `tests/integration/test_repositorio_listar_obter.py`: `listar` usa `ORDER BY nome, id`, `LIMIT 20`/`OFFSET` e `COUNT(*)`; nomes iguais têm ordem estável; `obter` decifra todos os campos corretamente; `obter` de id inexistente → `None`
- [X] T045 [P] [US2] Criar `tests/contract/test_get_clientes.py` (teste do endpoint GET lista): body `PaginaClientes` com `page_size == 20`, itens `ClienteResumo` com `documento_mascarado` (`***.982.247-**`) e sem campo `documento`; lista vazia → `items: []`, `total_items: 0`; `?page=99` → 200 vazio com totais; `?page=0` → 422; usar fixture `logs_sem_dados_pessoais`
- [X] T046 [P] [US2] Criar `tests/contract/test_get_cliente_por_id.py` (teste do endpoint GET item): 200 com `ClienteDetalhe` completo (documento formatado); UUID inexistente → 404 `cliente_nao_encontrado`; id não-UUID → 422

### Implementation for User Story 2

- [X] T047 [P] [US2] Implementar `src/cadastro_cliente/application/casos_de_uso/listar_clientes.py`: `ListarClientes(repo).executar(pagina: int) -> Pagina[Cliente]` com `TAMANHO_PAGINA = 20` (faz T042 passar)
- [X] T048 [P] [US2] Implementar `src/cadastro_cliente/application/casos_de_uso/obter_cliente.py`: `ObterCliente(repo).executar(id) -> Cliente` (faz T043 passar)
- [X] T049 [US2] Implementar `listar` e `obter` em `src/cadastro_cliente/infrastructure/db/repositorio_cliente.py` (faz T044 passar)
- [X] T050 [US2] Adicionar `ClienteResumo` e `PaginaClientes` em `src/cadastro_cliente/interfaces/api/schemas.py` conforme contracts/openapi.yaml
- [X] T051 [US2] Implementar `GET /clientes?page=` e `GET /clientes/{id}` em `src/cadastro_cliente/interfaces/api/rotas_clientes.py` (faz T045 e T046 passarem)

**Checkpoint**: US1 e US2 funcionam independentemente

---

## Phase 5: User Story 3 - Editar cliente (Priority: P3)

**Goal**: Operador atualiza dados de um cliente com as mesmas validações do cadastro, sem permitir documento duplicado.

**Independent Test**: `PUT /clientes/{id}` sobre cliente inserido via repositório aplica alterações válidas e recusa inválidas/duplicadas mantendo os dados — quickstart cenários 10, 11 e 14.

### Tests for User Story 3 ⚠️ (escrever primeiro, devem falhar)

- [X] T052 [P] [US3] Criar `tests/unit/application/test_editar_cliente.py`: altera e-mail válido; manter o próprio documento não é duplicidade; mudar para documento de outro cliente → `DocumentoDuplicadoError` e dados intactos; e-mail inválido → `DadosInvalidosError` e dados intactos; id inexistente → `ClienteNaoEncontradoError`; `atualizado_em` muda e `criado_em` não
- [X] T053 [P] [US3] Criar `tests/integration/test_repositorio_atualizar.py`: `atualizar` recifra os campos e recalcula `documento_hash`; atualizar para documento de outro cliente → `DocumentoDuplicadoError` (constraint) sem alterar a linha
- [X] T054 [P] [US3] Criar `tests/contract/test_put_cliente.py` (teste do endpoint PUT): 200 com dados novos; 409 ao usar CNPJ de outro cliente e `GET` posterior mostra dados originais; 422 com todos os erros e sem `input`; 404 para UUID inexistente; usar fixture `logs_sem_dados_pessoais`

### Implementation for User Story 3

- [X] T055 [US3] Implementar `src/cadastro_cliente/application/casos_de_uso/editar_cliente.py`: `EditarCliente(repo).executar(id, dados)` — `obter` (→ `ClienteNaoEncontradoError`), `cliente.atualizar(...)`, `existe_documento(doc, ignorar_id=id)` (→ `DocumentoDuplicadoError`), `repo.atualizar`; log apenas com `cliente_id` (faz T052 passar)
- [X] T056 [US3] Implementar `atualizar` em `src/cadastro_cliente/infrastructure/db/repositorio_cliente.py` com tradução de `IntegrityError` → `DocumentoDuplicadoError` (faz T053 passar)
- [X] T057 [US3] Implementar `PUT /clientes/{id}` em `src/cadastro_cliente/interfaces/api/rotas_clientes.py` retornando 200 com `ClienteDetalhe` (faz T054 passar)

**Checkpoint**: US1–US3 funcionam independentemente

---

## Phase 6: User Story 4 - Remover cliente (Priority: P4)

**Goal**: Operador remove definitivamente um cliente; o documento fica livre para novo cadastro.

**Independent Test**: `DELETE /clientes/{id}` sobre cliente inserido via repositório retorna 204 e o cliente some; documento pode ser recadastrado — quickstart cenários 12–14.

### Tests for User Story 4 ⚠️ (escrever primeiro, devem falhar)

- [X] T058 [P] [US4] Criar `tests/unit/application/test_remover_cliente.py`: remove existente; id inexistente → `ClienteNaoEncontradoError`; após remover, `CriarCliente` com o mesmo documento funciona
- [X] T059 [P] [US4] Criar `tests/integration/test_repositorio_remover.py`: `remover` faz `DELETE` físico (`SELECT count(*)` = 0 para o id, sem linha residual) e retorna `False` para id inexistente; reinserir o mesmo documento após remover é aceito
- [X] T060 [P] [US4] Criar `tests/contract/test_delete_cliente.py` (teste do endpoint DELETE): 204 sem body; `GET` posterior → 404; `POST` com o mesmo documento → 201; `DELETE` em UUID inexistente → 404 `cliente_nao_encontrado`; usar fixture `logs_sem_dados_pessoais`

### Implementation for User Story 4

- [X] T061 [US4] Implementar `src/cadastro_cliente/application/casos_de_uso/remover_cliente.py`: `RemoverCliente(repo).executar(id)` lançando `ClienteNaoEncontradoError` se `remover` retornar `False`; log apenas com `cliente_id` (faz T058 passar)
- [X] T062 [US4] Implementar `remover` em `src/cadastro_cliente/infrastructure/db/repositorio_cliente.py` com `DELETE` físico (faz T059 passar)
- [X] T063 [US4] Implementar `DELETE /clientes/{id}` em `src/cadastro_cliente/interfaces/api/rotas_clientes.py` retornando 204 (faz T060 passar)

**Checkpoint**: todas as user stories funcionais

---

## Phase 7: Polish & Cross-Cutting Concerns

**Purpose**: Verificações transversais de contrato, privacidade, desempenho e documentação

- [X] T064 [P] Criar `tests/contract/test_conformidade_openapi.py`: carrega `specs/001-cadastro-cliente/contracts/openapi.yaml` e compara com `app.openapi()` — mesmos paths, métodos e códigos de status documentados
- [X] T065 [P] Criar `tests/contract/test_privacidade_logs.py`: executa o fluxo completo (POST, GET lista, GET item, PUT, DELETE, erros 409/422/404) com `caplog` em nível DEBUG e verifica que nenhum CPF, CNPJ, e-mail ou telefone usado aparece em nenhum registro (SC-005)
- [X] T066 [P] Criar `tests/integration/test_desempenho_listagem.py` (marcador `integration`): insere 10.000 clientes e verifica que `GET /clientes?page=1` responde em ≤ 2 s (SC-004)
- [X] T067 Rodar `uv run ruff check . && uv run ruff format --check .` e corrigir apontamentos
- [X] T068 Rodar `uv run pytest` completo e garantir 100% verde
- [X] T069 Executar manualmente os 14 cenários e a verificação de privacidade de `specs/001-cadastro-cliente/quickstart.md` contra `uvicorn` + PostgreSQL do `docker-compose.yml`
- [X] T070 [P] Adicionar ao `README.md` uma seção "Rodando o módulo" apontando para `specs/001-cadastro-cliente/quickstart.md`

---

## Dependencies & Execution Order

### Phase Dependencies

- **Setup (Phase 1)**: sem dependências
- **Foundational (Phase 2)**: depende do Setup — BLOQUEIA todas as stories
- **User Stories (Phases 3–6)**: dependem da Foundational; independentes entre si
  (cada story popula seus dados de teste via repositório, sem depender de endpoints de outra)
- **Polish (Phase 7)**: depende de todas as stories

### Dependências internas relevantes

- T015–T018 → T019 (entidade usa todos os value objects)
- T019 → T020 → T022 (fake usa portas e entidade)
- T023 → T024, T028; T026 → T027, T029; T024 + T026 → T029
- T030 + T031 + T032 → T033 → T034
- Em cada story: testes → caso de uso → repositório → rota
- `repositorio_cliente.py` e `rotas_clientes.py` são editados por todas as stories: tarefas nesses
  arquivos em stories diferentes NÃO devem rodar em paralelo

### User Story Dependencies

- **US1 (P1)**: após Foundational — sem dependência de outras stories
- **US2 (P2)**: após Foundational — independente (dados criados via repositório)
- **US3 (P3)**: após Foundational — independente
- **US4 (P4)**: após Foundational — o teste de recadastro em T060 usa `POST` (US1); se executada antes de US1, esse caso específico fica pendente

---

## Parallel Example: Foundational

```bash
# Testes de domínio em paralelo:
Task: "tests/unit/domain/test_documento.py"     # T009
Task: "tests/unit/domain/test_contato.py"       # T010
Task: "tests/unit/domain/test_endereco.py"      # T011
Task: "tests/unit/domain/test_cliente.py"       # T012

# Value objects em paralelo (arquivos diferentes):
Task: "src/cadastro_cliente/domain/documento.py"  # T016
Task: "src/cadastro_cliente/domain/contato.py"    # T017
Task: "src/cadastro_cliente/domain/endereco.py"   # T018
```

## Parallel Example: User Story 2

```bash
# Todos os testes da US2 juntos:
Task: "tests/unit/application/test_listar_clientes.py"   # T042
Task: "tests/unit/application/test_obter_cliente.py"     # T043
Task: "tests/integration/test_repositorio_listar_obter.py"  # T044
Task: "tests/contract/test_get_clientes.py"              # T045
Task: "tests/contract/test_get_cliente_por_id.py"        # T046

# Casos de uso em paralelo:
Task: "src/cadastro_cliente/application/casos_de_uso/listar_clientes.py"  # T047
Task: "src/cadastro_cliente/application/casos_de_uso/obter_cliente.py"    # T048
```

---

## Implementation Strategy

### MVP First (User Story 1 Only)

1. Phase 1: Setup
2. Phase 2: Foundational (domínio + criptografia + model + migration + API base)
3. Phase 3: US1 (cadastro)
4. **STOP and VALIDATE**: quickstart cenários 1–6 e verificação de privacidade

### Incremental Delivery

1. Setup + Foundational → base pronta
2. US1 → validar → MVP
3. US2 → validar (listagem/consulta)
4. US3 → validar (edição)
5. US4 → validar (remoção)
6. Polish → conformidade de contrato, privacidade, desempenho

---

## Notes

- [P] = arquivos diferentes, sem dependência de tarefa incompleta
- Testes MUST falhar antes da implementação (Princípio II)
- Nunca usar documentos reais em testes — sempre `tests/fabricas.py`
- Nunca logar documento, e-mail, telefone ou endereço — apenas `cliente_id`
- Commit após cada tarefa ou grupo lógico; parar em cada checkpoint para validar

---

## Phase 8: Convergence

- [ ] T071 CRITICAL: Tornar estruturados (JSON) os logs dos loggers `uvicorn`, `uvicorn.error` e `uvicorn.access`, que hoje saem em texto simples (`INFO:     127.0.0.1:... "POST /clientes ..."`): em `configurar_logging()` de `src/cadastro_cliente/infrastructure/logging/sanitizador.py`, aplicar o `FormatadorJson` aos handlers desses loggers (ou fazê-los propagar para o handler JSON do root, mantendo o `FiltroDadosSensiveis`); adicionar teste em `tests/unit/infrastructure/test_sanitizador.py` que valida JSON para um registro de acesso, per Constitution "Requisitos de Segurança e Privacidade" (logging MUST ser estruturado) (contradicts)
- [ ] T072 Reportar erros de forma (tipo) e de regra de negócio na mesma resposta 422: hoje um payload com `nome` de tipo inválido e `documento`/`email`/`telefone`/`endereco` inválidos retorna apenas `nome`; ajustar `src/cadastro_cliente/interfaces/api/schemas.py` + `src/cadastro_cliente/interfaces/api/erros.py` para que campos com tipo inválido virem `formato_invalido` e os demais campos ainda passem pela validação do domínio, com teste em `tests/contract/test_post_clientes.py` e `tests/contract/test_put_cliente.py`, per FR-010 (partial)
- [ ] T073 Documentar os requisitos de ambiente de produção que o código pressupõe: criptografia de disco/volume do PostgreSQL (mitigação do `nome` sem cifra de aplicação, plan.md Complexity Tracking) e terminação TLS no proxy/ingress, em uma seção "Implantação em produção" de `specs/001-cadastro-cliente/quickstart.md` (ou `docs/implantacao.md` referenciado pelo `README.md`), per Constitution IV (criptografia em repouso, TLS) / plan: Storage (partial)
- [ ] T074 Validar as chaves na inicialização: `criar_app()` em `src/cadastro_cliente/main.py` deve carregar `get_settings()` (ou um evento de startup) para que a aplicação falhe ao iniciar sem `CADASTRO_ENCRYPTION_KEY`/`CADASTRO_HMAC_KEY` válidas — hoje sobe normalmente e só falha (500) na primeira requisição; ajustar a fixture `client` de `tests/conftest.py` para fornecer settings de teste e adicionar teste em `tests/unit/infrastructure/test_protetor_dados.py`, per plan: research R5 ("Aplicação falha ao iniciar sem elas") (partial)
- [ ] T075 Alinhar `specs/001-cadastro-cliente/contracts/openapi.yaml` ao comportamento implementado: documentar `422` (id não-UUID) em `GET`/`DELETE /clientes/{id}`, a resposta `500` com `code: erro_interno` e os códigos `formato_invalido` e `pagina_invalida`; registrar esses códigos na tabela "Códigos de erro de domínio" de `specs/001-cadastro-cliente/data-model.md`, per plan: contracts/openapi.yaml, R12 (unrequested)
