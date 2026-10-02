# Data Model: Cadastro de Cliente

**Feature**: [spec.md](./spec.md) | **Research**: [research.md](./research.md)

## Domínio

### Entidade `Cliente`

| Campo | Tipo (domínio) | Regras |
|-------|----------------|--------|
| `id` | UUID | Gerado na criação (uuid4); imutável |
| `nome` | str | Obrigatório; `strip()`; 2–150 caracteres; só espaços = vazio |
| `documento` | `Documento` | Obrigatório; ver value object |
| `tipo_pessoa` | `TipoPessoa` (`FISICA` \| `JURIDICA`) | Derivado de `documento` (não informado pelo usuário) |
| `email` | `Email` | Obrigatório; ver value object |
| `telefone` | `Telefone` | Obrigatório; ver value object |
| `endereco` | `Endereco` | Obrigatório; ver value object |
| `criado_em` | datetime (UTC) | Definido na criação |
| `atualizado_em` | datetime (UTC) | Atualizado a cada edição |

**Invariantes**: um `Cliente` só existe com todos os value objects válidos. A criação/edição
valida todos os campos e reporta **todos** os erros juntos (`DadosInvalidosError`, FR-010).

### Value object `Documento` (FR-002 a FR-004, Princípio III)

- Entrada: string com ou sem pontuação; normalizada para somente dígitos.
- 11 dígitos → CPF (`FISICA`); 14 dígitos → CNPJ (`JURIDICA`); outro tamanho → `documento_invalido`.
- Todos os dígitos iguais → `documento_invalido`.
- Dígitos verificadores (módulo 11) incorretos → `documento_invalido`.
- Expõe: `valor` (dígitos), `tipo`, `formatado()` (`529.982.247-25` / `11.222.333/0001-81`),
  `mascarado()`.
- Máscara: CPF `***.982.247-**`; CNPJ `**.222.333/0001-**`.
- `__repr__`/`__str__` retornam a forma mascarada (evita vazamento acidental em logs).

### Value object `Email` (FR-006)

- `strip()`; obrigatório; máx. 254 caracteres; normalizado para minúsculas.
- Formato: `parte-local@dominio.tld` — exatamente um `@`, parte local não vazia sem espaços,
  domínio com ao menos um ponto, rótulos não vazios. Inválido → `email_invalido`.
- Não precisa ser único (Assumptions da spec).

### Value object `Telefone` (FR-007)

- Normalizado para somente dígitos; 10 ou 11 dígitos; DDD (2 primeiros dígitos) entre 11 e 99
  sem zero na primeira posição. Inválido → `telefone_invalido`.
- `formatado()`: `(11) 98765-4321` / `(11) 3456-7890`.

### Value object `Endereco` (FR-009)

| Campo | Regras |
|-------|--------|
| `logradouro` | Obrigatório; 1–200 |
| `numero` | Obrigatório; 1–20 (aceita "S/N") |
| `complemento` | Opcional; 0–100; vazio → `None` |
| `bairro` | Obrigatório; 1–100 |
| `cidade` | Obrigatório; 1–100 |
| `uf` | Obrigatório; uma das 27 siglas; normalizada para maiúsculas |
| `cep` | Obrigatório; 8 dígitos após remover pontuação |

Erros por subcampo usam `field` com caminho: `endereco.cep`, `endereco.uf`, etc.

### Códigos de erro de domínio

| Código | Campo | Situação |
|--------|-------|----------|
| `obrigatorio` | qualquer | Ausente ou só espaços |
| `tamanho_invalido` | texto | Fora dos limites |
| `documento_invalido` | `documento` | Tamanho, dígitos iguais ou DV incorreto |
| `documento_duplicado` | `documento` | Já existe outro cliente com o documento (409) |
| `email_invalido` | `email` | Formato inválido |
| `telefone_invalido` | `telefone` | Tamanho ou DDD inválido |
| `cep_invalido` | `endereco.cep` | ≠ 8 dígitos |
| `uf_invalida` | `endereco.uf` | Sigla inexistente |
| `cliente_nao_encontrado` | — | ID inexistente (404) |

### Ciclo de vida

```text
(inexistente) --criar--> CADASTRADO --editar--> CADASTRADO
                              |
                              +--remover--> (apagado definitivamente; documento liberado)
```

Não há estados intermediários nem exclusão lógica (clarificação 2026-10-02).

## Portas (camada de aplicação)

- `ClienteRepository`: `adicionar(cliente)`, `atualizar(cliente)`, `obter(id) -> Cliente | None`,
  `remover(id) -> bool`, `existe_documento(documento, ignorar_id=None) -> bool`,
  `listar(pagina, tamanho) -> Pagina[Cliente]`. Lança `DocumentoDuplicadoError` se a constraint
  de unicidade falhar.
- `Pagina[T]`: `itens`, `pagina`, `tamanho`, `total_itens`, `total_paginas`.

## Persistência (PostgreSQL)

Tabela `clientes`:

| Coluna | Tipo | Restrições | Observação |
|--------|------|------------|------------|
| `id` | `uuid` | PK | |
| `nome` | `varchar(150)` | NOT NULL | Texto (ordenação); índice `ix_clientes_nome (nome, id)` |
| `tipo_pessoa` | `varchar(8)` | NOT NULL, CHECK in (`FISICA`,`JURIDICA`) | |
| `documento_hash` | `bytea` (32) | NOT NULL, UNIQUE | HMAC-SHA256 do documento normalizado |
| `documento_cifrado` | `bytea` | NOT NULL | AES-256-GCM (`nonce‖ciphertext`) |
| `email_cifrado` | `bytea` | NOT NULL | AES-256-GCM |
| `telefone_cifrado` | `bytea` | NOT NULL | AES-256-GCM |
| `endereco_cifrado` | `bytea` | NOT NULL | AES-256-GCM sobre JSON do endereço |
| `criado_em` | `timestamptz` | NOT NULL | |
| `atualizado_em` | `timestamptz` | NOT NULL | |

- Mapeamento entidade ↔ linha é feito no repositório de infraestrutura usando a porta
  `ProtetorDados` (`cifrar`, `decifrar`, `hash_documento`); o domínio desconhece a criptografia.
- Remoção: `DELETE FROM clientes WHERE id = :id` (física).
- Migration inicial via Alembic cria tabela e índices.
