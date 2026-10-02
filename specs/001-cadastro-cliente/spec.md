# Feature Specification: Cadastro de Cliente

**Feature Branch**: `001-cadastro-cliente` (nenhuma branch criada; trabalho atual em `main`)

**Created**: 2026-10-02

**Status**: Draft

**Input**: User description: "Quero um módulo de cadastro de cliente: criar, listar, editar e remover clientes. Cada cliente tem nome, CPF ou CNPJ (não pode repetir), e-mail, telefone e endereço. O sistema deve impedir cadastro duplicado pelo mesmo CPF/CNPJ e validar e-mail."

## Clarifications

### Session 2026-10-02

- Q: CPF e CNPJ devem ser guardados num único campo "documento" ou em dois campos separados? → A: Campo único "documento"; tipo de pessoa inferido pela quantidade de dígitos (11 = CPF, 14 = CNPJ); unicidade por documento.
- Q: O endereço deve ser obrigatório no cadastro do cliente? → A: Sim, obrigatório e completo (logradouro, número, bairro, cidade, UF e CEP); apenas complemento é opcional.
- Q: Como a listagem de clientes deve ser dividida em páginas? → A: Páginas fixas de 20 clientes, ordenadas por nome, exibindo total de registros e de páginas.
- Q: Ao remover um cliente, os dados devem ser apagados de vez ou só marcados como removidos? → A: Exclusão definitiva; dados pessoais apagados e documento liberado para novo cadastro.

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Cadastrar cliente (Priority: P1)

Um operador do sistema registra um novo cliente informando nome, documento (CPF para pessoa física
ou CNPJ para pessoa jurídica), e-mail, telefone e endereço. O sistema confere se os dados são
válidos e se já não existe outro cliente com o mesmo documento antes de concluir o cadastro.

**Why this priority**: sem o cadastro não existe nenhum cliente para listar, editar ou remover; é a
fatia mínima que já entrega valor (registrar clientes de forma confiável e sem duplicidade).

**Independent Test**: pode ser testado cadastrando clientes válidos e inválidos e verificando que
apenas os válidos e não duplicados são aceitos.

**Acceptance Scenarios**:

1. **Given** nenhum cliente com o CPF `529.982.247-25`, **When** o operador cadastra um cliente com
   esse CPF e demais dados válidos, **Then** o cliente é registrado e o sistema confirma o cadastro.
2. **Given** nenhum cliente com o CNPJ informado, **When** o operador cadastra uma empresa com CNPJ
   válido, **Then** o cliente é registrado como pessoa jurídica.
3. **Given** um cliente já cadastrado com o CPF `529.982.247-25`, **When** o operador tenta cadastrar
   outro cliente com `52998224725` (mesmo número sem pontuação), **Then** o cadastro é recusado com
   a mensagem de que o documento já está cadastrado.
4. **Given** o formulário de cadastro, **When** o operador informa um CPF/CNPJ com dígitos
   verificadores incorretos, **Then** o cadastro é recusado indicando documento inválido.
5. **Given** o formulário de cadastro, **When** o operador informa um e-mail em formato inválido
   (ex.: `joao@`), **Then** o cadastro é recusado indicando e-mail inválido.
6. **Given** o formulário de cadastro, **When** o operador deixa um campo obrigatório em branco,
   **Then** o cadastro é recusado indicando quais campos precisam ser preenchidos.

---

### User Story 2 - Listar e consultar clientes (Priority: P2)

O operador visualiza a lista de clientes cadastrados e consegue abrir os dados de um cliente
específico.

**Why this priority**: permite verificar os cadastros feitos e é pré-requisito prático para editar
e remover.

**Independent Test**: com clientes previamente cadastrados, verificar que a listagem mostra todos
eles e que a consulta individual retorna os dados corretos.

**Acceptance Scenarios**:

1. **Given** 3 clientes cadastrados, **When** o operador acessa a listagem, **Then** os 3 clientes
   são exibidos com nome, documento mascarado, e-mail e telefone.
2. **Given** nenhum cliente cadastrado, **When** o operador acessa a listagem, **Then** o sistema
   informa que não há clientes cadastrados.
3. **Given** mais clientes do que cabem em uma página, **When** o operador acessa a listagem,
   **Then** os resultados são apresentados em páginas de 20 clientes, com o total de clientes e de
   páginas.
4. **Given** um cliente cadastrado, **When** o operador consulta esse cliente, **Then** todos os
   seus dados são exibidos.

---

### User Story 3 - Editar cliente (Priority: P3)

O operador corrige ou atualiza os dados de um cliente existente.

**Why this priority**: dados de contato mudam com o tempo; é importante, mas o sistema já tem valor
sem esta capacidade.

**Independent Test**: editar um cliente existente e verificar que as alterações válidas são
persistidas e as inválidas são recusadas.

**Acceptance Scenarios**:

1. **Given** um cliente cadastrado, **When** o operador altera o e-mail para outro e-mail válido,
   **Then** o novo e-mail é salvo e passa a ser exibido.
2. **Given** dois clientes A e B, **When** o operador altera o documento de A para o documento de B,
   **Then** a alteração é recusada por duplicidade e os dados de A permanecem inalterados.
3. **Given** um cliente cadastrado, **When** o operador salva a edição com e-mail inválido,
   **Then** a alteração é recusada e os dados anteriores são mantidos.
4. **Given** um cliente que foi removido, **When** o operador tenta editá-lo, **Then** o sistema
   informa que o cliente não foi encontrado.

---

### User Story 4 - Remover cliente (Priority: P4)

O operador remove um cliente que não deve mais constar no cadastro.

**Why this priority**: necessário para manter a base limpa e atender pedidos de exclusão de dados,
mas é a operação menos frequente.

**Independent Test**: remover um cliente existente e verificar que ele deixa de aparecer na
listagem e na consulta.

**Acceptance Scenarios**:

1. **Given** um cliente cadastrado, **When** o operador solicita a remoção e confirma, **Then** o
   cliente deixa de aparecer na listagem e na consulta.
2. **Given** um cliente cadastrado, **When** o operador solicita a remoção e cancela a confirmação,
   **Then** o cliente permanece cadastrado.
3. **Given** um cliente removido, **When** o operador cadastra um novo cliente com o mesmo
   documento, **Then** o cadastro é aceito.
4. **Given** um identificador de cliente inexistente, **When** o operador tenta removê-lo,
   **Then** o sistema informa que o cliente não foi encontrado.

---

### Edge Cases

- Documento informado com ou sem pontuação (`529.982.247-25` vs `52998224725`) MUST ser tratado
  como o mesmo documento para fins de unicidade.
- CPF ou CNPJ com todos os dígitos iguais (ex.: `000.000.000-00`) é recusado mesmo que o cálculo
  dos dígitos verificadores "feche".
- Documento com quantidade de dígitos diferente de 11 (CPF) ou 14 (CNPJ) é recusado.
- Dois cadastros simultâneos com o mesmo documento: apenas um MUST ser aceito.
- E-mail com espaços no início/fim é aceito após remoção dos espaços; e-mail sem `@` ou sem
  domínio é recusado.
- Nome composto apenas por espaços é tratado como campo em branco.
- Mensagens de erro de duplicidade ou validação MUST NOT exibir o documento completo de outro
  cliente.

## Requirements *(mandatory)*

### Functional Requirements

**Cadastro**

- **FR-001**: O sistema MUST permitir cadastrar um cliente com nome, documento (CPF ou CNPJ),
  e-mail, telefone e endereço.
- **FR-002**: CPF e CNPJ MUST ser informados em um único campo "documento". O sistema MUST
  identificar o tipo pela quantidade de dígitos (11 = CPF/pessoa física, 14 = CNPJ/pessoa
  jurídica), sem seletor de tipo para o operador.
- **FR-003**: O sistema MUST validar CPF e CNPJ pelos dígitos verificadores e recusar documentos
  com todos os dígitos iguais.
- **FR-004**: O sistema MUST desconsiderar pontuação ao comparar e armazenar documentos.
- **FR-005**: O sistema MUST impedir que dois clientes possuam o mesmo documento, tanto no
  cadastro quanto na edição.
- **FR-006**: O sistema MUST validar o formato do e-mail (parte local, `@` e domínio com ponto).
- **FR-007**: O sistema MUST validar o telefone como número brasileiro com DDD (10 ou 11 dígitos,
  desconsiderando pontuação).
- **FR-008**: Nome, documento, e-mail, telefone e endereço MUST ser obrigatórios.
- **FR-009**: O endereço é obrigatório e MUST conter logradouro, número, bairro, cidade, UF e CEP;
  apenas o complemento é opcional. Cadastro ou edição com qualquer parte obrigatória ausente MUST
  ser recusado. CEP MUST ter 8 dígitos e UF MUST ser uma sigla válida.
- **FR-010**: Ao recusar uma operação, o sistema MUST informar todos os campos com problema e o
  motivo de cada um.

**Consulta**

- **FR-011**: O sistema MUST listar os clientes em páginas de tamanho fixo de 20 itens, ordenados
  por nome, informando o total de clientes e de páginas. Solicitar uma página além da última MUST
  retornar uma página vazia com os totais corretos.
- **FR-012**: A listagem MUST exibir o documento mascarado (ex.: `***.982.247-**`).
- **FR-013**: O sistema MUST permitir consultar os dados completos de um cliente específico.

**Edição e remoção**

- **FR-014**: O sistema MUST permitir editar qualquer dado de um cliente existente, aplicando as
  mesmas validações do cadastro.
- **FR-015**: O sistema MUST permitir remover um cliente mediante confirmação explícita.
- **FR-016**: A remoção MUST ser definitiva: todos os dados do cliente (incluindo dados pessoais
  e endereço) MUST ser apagados, sem exclusão lógica nem cópia retida, e o documento MUST ficar
  disponível para novo cadastro.
- **FR-017**: Operações sobre cliente inexistente MUST retornar a indicação "cliente não
  encontrado".

**Privacidade e segurança** (conforme constituição, Princípios III e IV)

- **FR-018**: CPF, CNPJ, e-mail e telefone MUST NOT ser registrados em texto claro em logs ou
  mensagens de erro técnicas.
- **FR-019**: Os dados pessoais do cliente MUST ser armazenados protegidos (criptografados).

### Key Entities *(include if feature involves data)*

- **Cliente**: pessoa física ou jurídica cadastrada. Atributos: identificador, nome (ou razão
  social), documento, tipo de pessoa (física/jurídica, derivado do documento), e-mail, telefone,
  endereço, data de criação e data da última atualização.
- **Documento (CPF/CNPJ)**: identificador fiscal do cliente; único entre clientes cadastrados; sempre
  válido e normalizado; dado sensível.
- **Endereço**: logradouro, número, complemento (opcional), bairro, cidade, UF e CEP; pertence a
  um único cliente.

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: Um operador consegue cadastrar um novo cliente em menos de 2 minutos.
- **SC-002**: 100% das tentativas de cadastro ou edição com documento já existente (com ou sem
  pontuação) são recusadas.
- **SC-003**: 100% dos CPFs/CNPJs e e-mails inválidos do conjunto de casos de teste são recusados,
  e 100% dos válidos são aceitos.
- **SC-004**: A listagem exibe a primeira página em até 2 segundos com até 10.000 clientes
  cadastrados.
- **SC-005**: Nenhum CPF, CNPJ, e-mail ou telefone completo aparece nos logs gerados durante a
  execução dos cenários de aceitação.
- **SC-006**: 90% dos operadores concluem o primeiro cadastro sem ajuda, guiados apenas pelas
  mensagens do sistema.

## Assumptions

- Os usuários do módulo são operadores internos já autenticados; autenticação e perfis de acesso
  estão fora do escopo desta feature.
- Cada cliente tem exatamente um e-mail, um telefone e um endereço (múltiplos contatos/endereços
  fora do escopo).
- E-mail não precisa ser único entre clientes (ex.: empresas do mesmo grupo podem compartilhar).
- Validação de e-mail é apenas de formato; não há envio de e-mail de confirmação.
- Endereço é preenchido manualmente; consulta automática de CEP está fora do escopo.
- Histórico/auditoria de clientes removidos está fora do escopo (consequência da exclusão
  definitiva, alinhada ao direito de eliminação da LGPD).
- Busca e filtros na listagem ficam para uma feature futura.
- Volume esperado: até 10.000 clientes.
