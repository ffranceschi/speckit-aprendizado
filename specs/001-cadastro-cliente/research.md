# Research: Cadastro de Cliente

**Feature**: [spec.md](./spec.md) | **Plan**: [plan.md](./plan.md) | **Date**: 2026-10-02

Stack definida pelo usuário: Python + FastAPI, PostgreSQL, SQLAlchemy, Pydantic, pytest. As
decisões abaixo resolvem os pontos em aberto do Technical Context e as exigências da constituição.

## R1. Versões e ferramentas base

- **Decision**: Python 3.12; FastAPI; SQLAlchemy 2.x (API síncrona, `Session`) com driver
  psycopg 3; Alembic para migrations; Pydantic v2 + pydantic-settings; `cryptography` para
  criptografia; gerenciamento de dependências com `uv`; lint/format com Ruff.
- **Rationale**: versões estáveis e amplamente documentadas. API síncrona do SQLAlchemy é mais
  simples de testar e suficiente para o volume (≤ 10.000 clientes, operadores internos).
  `uv` já é usado no projeto para instalar o Spec Kit.
- **Alternatives considered**: SQLAlchemy async + asyncpg (mais complexidade de sessão e testes sem
  ganho real neste volume); Poetry (mais lento, `uv` já disponível).

## R2. Arquitetura em camadas (Constituição, Princípio I)

- **Decision**: pacote único `cadastro_cliente` com quatro subpacotes: `domain` (entidade
  `Cliente`, value objects `Documento`, `Email`, `Telefone`, `Endereco`, erros de domínio),
  `application` (casos de uso + porta `ClienteRepository` e porta `ProtetorDados`),
  `interfaces/api` (rotas FastAPI, schemas Pydantic, mapeamento de erros) e `infrastructure`
  (modelos SQLAlchemy, repositório concreto, criptografia, logging, configuração).
- **Rationale**: domínio e casos de uso ficam livres de FastAPI/SQLAlchemy/Pydantic e são
  testáveis com dublês em memória (Princípio II).
- **Alternatives considered**: usar modelos Pydantic/SQLAlchemy como entidades de domínio
  (rejeitado: acopla regra de negócio ao framework, viola Princípio I).

## R3. Onde validar (Pydantic vs domínio)

- **Decision**: schemas Pydantic validam apenas **forma** (tipos, campos presentes, strings). Toda
  regra de negócio — dígitos verificadores, formato de e-mail, telefone, CEP, UF, obrigatoriedade
  após `strip()` — fica nos value objects do domínio. O caso de uso coleta **todos** os erros de
  campo e lança um único `DadosInvalidosError` com a lista (FR-010).
- **Rationale**: a regra continua válida se a interface mudar (CLI, fila); os testes de domínio
  cobrem 100% das regras sem HTTP.
- **Alternatives considered**: `EmailStr`/validators Pydantic (rejeitado como fonte da regra:
  coloca regra de negócio na camada de interface e dificulta agregar erros no formato da spec).

## R4. Validação de CPF/CNPJ

- **Decision**: value object `Documento` normaliza para somente dígitos; 11 dígitos → CPF,
  14 → CNPJ, outro tamanho → inválido; rejeita sequências de dígitos iguais; calcula dígitos
  verificadores pelo algoritmo módulo 11 (pesos 10..2/11..2 para CPF; 5..2,9..2 / 6..2,9..2 para
  CNPJ). Implementação própria, sem biblioteca externa.
- **Rationale**: algoritmo curto e estável; implementação própria evita dependência e deixa a regra
  explícita e testada (Princípio III). CNPJ alfanumérico (previsto pela Receita) está fora do escopo
  da spec (que fala em dígitos) — registrado como evolução futura.
- **Alternatives considered**: `validate-docbr` / `brazilnum` (dependência extra para ~40 linhas).

## R5. Proteção dos dados pessoais em repouso (Princípio IV, FR-019)

- **Decision**:
  - `documento`, `email`, `telefone` e `endereco` são criptografados na aplicação com
    **AES-256-GCM** (`cryptography.hazmat.primitives.ciphers.aead.AESGCM`), nonce aleatório de
    12 bytes por valor, armazenados como `bytea` (`nonce || ciphertext`). O endereço é
    serializado em JSON antes de criptografar.
  - Unicidade usa coluna `documento_hash` = **HMAC-SHA256**(chave HMAC, documento normalizado),
    com índice `UNIQUE` no banco.
  - `nome` fica em texto no banco para permitir ordenação/paginação por nome (FR-011); a proteção
    dele é a criptografia de volume/disco do PostgreSQL (requisito de ambiente) e a ausência em
    logs. Justificado em Complexity Tracking.
  - Chaves (`CADASTRO_ENCRYPTION_KEY`, `CADASTRO_HMAC_KEY`, 32 bytes em base64) vêm de variáveis
    de ambiente via pydantic-settings; nunca versionadas. Aplicação falha ao iniciar sem elas.
- **Rationale**: atende "criptografia em repouso" + "HMAC para busca/unicidade" exigidos pela
  constituição; GCM fornece confidencialidade e integridade; HMAC com chave impede ataque de
  dicionário sobre CPFs (espaço de CPF é pequeno — hash sem chave seria reversível).
- **Alternatives considered**: `pgcrypto` no banco (chave trafega em SQL e pode aparecer em logs do
  PostgreSQL); somente criptografia de disco (não protege contra dump/backup ou acesso SQL);
  SHA-256 sem chave para unicidade (vulnerável a força bruta); criptografar `nome` (impede
  ordenação no banco; exigiria ordenar em memória — inviável para paginação).
- **Evolução**: rotação de chaves (coluna `key_version`) fica fora do escopo desta feature.

## R6. Unicidade e concorrência (FR-005, edge case de cadastros simultâneos)

- **Decision**: o caso de uso verifica existência via `documento_hash` para devolver erro amigável,
  e o índice `UNIQUE (documento_hash)` é a garantia final: `IntegrityError` no commit é traduzido
  pelo repositório para `DocumentoDuplicadoError`. Edições concorrentes do mesmo cliente: última
  gravação vence (sem controle otimista nesta versão).
- **Rationale**: a checagem prévia sozinha tem condição de corrida; a constraint do banco é
  atômica.
- **Alternatives considered**: lock pessimista / `SERIALIZABLE` (custo e complexidade
  desnecessários); controle otimista com `version` (fora do escopo; spec não pede).

## R7. Logging sem dados sensíveis (Princípio IV, FR-018)

- **Decision**: logging estruturado (JSON) com um `logging.Filter` sanitizador aplicado ao root
  logger que mascara padrões de CPF, CNPJ, e-mail e telefone na mensagem e nos argumentos; código
  da aplicação loga apenas `cliente_id` (UUID). Handler de `RequestValidationError` do FastAPI é
  substituído para **não ecoar o campo `input`** que o Pydantic inclui por padrão nos erros 422.
  Logs de acesso do Uvicorn não registram corpo de requisição (padrão) e o `id` na URL é UUID.
- **Rationale**: defesa em profundidade — não logar dado pessoal por convenção e mascarar caso
  escape. O eco de `input` no 422 é um vazamento comum e fácil de esquecer.
- **Alternatives considered**: apenas convenção de código (frágil); structlog (dependência extra;
  `logging` + filtro atende).

## R8. Paginação (FR-011)

- **Decision**: `GET /clientes?page=N` (1-based, padrão 1), tamanho fixo 20, `ORDER BY nome, id`,
  `LIMIT/OFFSET`, `COUNT(*)` para totais. Resposta com `items`, `page`, `page_size`,
  `total_items`, `total_pages`. Página além da última → `items: []` com totais corretos;
  `page < 1` → 422.
- **Rationale**: simples e suficiente para 10.000 registros com índice em `nome`; o desempate por
  `id` torna a ordenação estável.
- **Alternatives considered**: paginação por cursor/keyset (melhor em volumes grandes, mas não
  entrega número de páginas, exigido pela clarificação).

## R9. Remoção definitiva (FR-016)

- **Decision**: `DELETE /clientes/{id}` executa `DELETE` físico da linha; `204` em sucesso, `404`
  se inexistente. A "confirmação explícita" é responsabilidade do cliente da API (UI), já que esta
  feature entrega apenas o backend.
- **Rationale**: decisão da clarificação (exclusão definitiva, sem cópia retida).
- **Alternatives considered**: soft delete (rejeitado na clarificação).

## R10. Edição (FR-014)

- **Decision**: `PUT /clientes/{id}` com substituição completa do recurso, mesmas validações do
  cadastro; se o documento mudar, revalida unicidade (ignorando o próprio cliente).
- **Rationale**: um único formato de payload para criar e editar; o formulário de edição sempre
  tem todos os campos.
- **Alternatives considered**: `PATCH` parcial (mais combinações de validação a testar, sem
  necessidade na spec).

## R11. Estratégia de testes (Princípio II)

- **Decision**:
  - `tests/unit/domain`: value objects e entidade — casos válidos/inválidos de CPF, CNPJ, e-mail,
    telefone, CEP, UF, máscara.
  - `tests/unit/application`: casos de uso com repositório em memória e protetor de dados fake.
  - `tests/integration`: repositório SQLAlchemy + criptografia contra PostgreSQL real
    (testcontainers), incluindo constraint de unicidade concorrente.
  - `tests/contract`: endpoints via `TestClient` validando status/payload contra
    `contracts/openapi.yaml`, incluindo teste que captura logs (`caplog`) e garante ausência de
    dados pessoais (SC-005).
  - Documentos de teste gerados por função utilitária (fictícios), nunca reais.
- **Rationale**: domínio/aplicação rodam em milissegundos sem infraestrutura; integração cobre o
  que só o banco garante.
- **Alternatives considered**: SQLite nos testes de integração (comportamento de `bytea`, índices
  e erros de integridade difere do PostgreSQL).

## R12. Formato de erro

- **Decision**: corpo único para erros de negócio:
  `{"errors": [{"field": "<campo>", "code": "<codigo>", "message": "<texto pt-BR>"}]}`.
  422 = dados inválidos (todos os campos com problema); 409 = documento duplicado; 404 = cliente
  não encontrado. Mensagens nunca incluem o valor informado.
- **Rationale**: atende FR-010 (todos os campos + motivo) e o edge case de não expor documento.
