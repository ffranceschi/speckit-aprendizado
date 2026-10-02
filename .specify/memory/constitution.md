<!--
Sync Impact Report
==================
Version change: (template, unversioned) → 1.0.0
Bump rationale: first ratification of the constitution (all placeholders filled).

Modified principles (placeholder → new title):
- [PRINCIPLE_1_NAME] → I. Clean Architecture
- [PRINCIPLE_2_NAME] → II. Testes Automatizados para Regras de Negócio (NÃO NEGOCIÁVEL)
- [PRINCIPLE_3_NAME] → III. Validação de Dados Pessoais (CPF/CNPJ)
- [PRINCIPLE_4_NAME] → IV. Proteção de Dados Sensíveis (Armazenamento e Logs)
- [PRINCIPLE_5_NAME] → removed (project defines 4 principles; Simplicity folded into Governance)

Added sections:
- Requisitos de Segurança e Privacidade (was [SECTION_2_NAME])
- Fluxo de Desenvolvimento e Quality Gates (was [SECTION_3_NAME])

Removed sections: none

Templates reviewed (read at runtime, not modified by this command):
- .specify/templates/plan-template.md ("Constitution Check" gate) — compatible
- .specify/templates/spec-template.md — compatible
- .specify/templates/tasks-template.md — compatible (tests are mandatory for business rules)

Follow-up TODOs: none
-->

# Cadastro de Cliente Constitution

## Core Principles

### I. Clean Architecture

O código MUST ser organizado em camadas com dependências apontando sempre para dentro:

- **Domínio** (entidades, value objects, regras de negócio): MUST NOT depender de framework,
  banco de dados, HTTP ou qualquer biblioteca de infraestrutura.
- **Aplicação** (casos de uso): orquestra o domínio e depende apenas de abstrações (interfaces/
  portas) para persistência e serviços externos.
- **Interface/Adaptadores** (controllers, DTOs, presenters): convertem dados externos para o
  formato dos casos de uso e vice-versa.
- **Infraestrutura** (ORM, repositórios concretos, frameworks web, logging): implementa as
  portas definidas nas camadas internas.

Regras de negócio MUST NOT residir em controllers, rotas, modelos de ORM ou migrations.
Toda violação da regra de dependência MUST ser justificada na seção "Complexity Tracking" do plano.

**Rationale**: isolar o domínio permite testá-lo sem infraestrutura e trocar tecnologias
(banco, framework) sem reescrever regras de negócio.

### II. Testes Automatizados para Regras de Negócio (NÃO NEGOCIÁVEL)

- Toda regra de negócio (validações, invariantes de entidades, casos de uso) MUST ter testes
  automatizados cobrindo o caminho de sucesso e os casos de erro relevantes.
- Testes de domínio e de casos de uso MUST executar sem banco de dados, rede ou framework web
  (usando dublês para as portas).
- Uma alteração em regra de negócio MUST NOT ser integrada sem o teste correspondente; os testes
  MUST passar no pipeline antes do merge.
- Endpoints/adaptadores SHOULD ter testes de integração para os fluxos principais.

**Rationale**: as regras de negócio são o ativo central do sistema; testes automatizados são a
única forma verificável de garantir que continuam corretas a cada mudança.

### III. Validação de Dados Pessoais (CPF/CNPJ)

- CPF e CNPJ MUST ser validados no domínio (formato, tamanho e dígitos verificadores) antes de
  qualquer persistência ou uso em regra de negócio.
- Documentos com todos os dígitos iguais (ex.: `111.111.111-11`) MUST ser rejeitados.
- O valor MUST ser normalizado (somente dígitos) antes de comparação, unicidade ou armazenamento.
- A validação MUST ser encapsulada em um value object (ou equivalente) para que nenhum CPF/CNPJ
  inválido exista no domínio.
- Toda regra de validação de CPF/CNPJ MUST ter testes com casos válidos e inválidos (Princípio II).

**Rationale**: dados pessoais inválidos corrompem a unicidade de cadastros e propagam erros para
integrações; centralizar a validação no domínio impede inconsistências.

### IV. Proteção de Dados Sensíveis (Armazenamento e Logs)

- CPF, CNPJ e demais dados pessoais MUST NOT aparecer em texto claro em logs, mensagens de erro,
  traces, métricas ou respostas de exceção. Quando necessário para diagnóstico, MUST ser
  mascarados (ex.: `***.***.789-**`) ou substituídos por identificador não sensível.
- Dados pessoais MUST ser armazenados com proteção adequada: criptografia em repouso e, quando for
  necessário buscar/garantir unicidade, um hash determinístico com chave secreta (ex.: HMAC) em
  vez do valor em claro como chave de busca.
- Chaves e segredos MUST NOT ser versionados no repositório; MUST vir de variáveis de ambiente ou
  gerenciador de segredos.
- Comunicação que trafega dados pessoais MUST usar canal criptografado (TLS).
- Dados de teste MUST usar documentos fictícios gerados, nunca dados reais de pessoas.

**Rationale**: vazamento de dados pessoais por logs e bancos mal protegidos é um dos riscos mais
comuns e tem implicações legais (LGPD); a proteção MUST ser padrão, não opcional.

## Requisitos de Segurança e Privacidade

- O tratamento de dados pessoais MUST seguir os princípios da LGPD (Lei nº 13.709/2018):
  finalidade, necessidade e segurança — coletar apenas os dados exigidos pela spec.
- O logging MUST ser estruturado e passar por um filtro/sanitizador que mascare campos sensíveis
  conhecidos (CPF, CNPJ, e-mail, telefone) antes da emissão.
- Respostas de API MUST NOT expor detalhes internos (stack traces, queries) que contenham dados
  pessoais.
- Toda feature que introduza um novo dado pessoal MUST declarar, na spec ou no plano, como ele
  será validado, armazenado e mascarado.

## Fluxo de Desenvolvimento e Quality Gates

- Toda feature segue o fluxo Spec Kit: `specify` → `clarify` → `plan` → `tasks` → `implement`.
- O plano MUST passar pelo "Constitution Check" antes da fase de design e novamente após ela;
  violações MUST ser justificadas ou corrigidas.
- A lista de tarefas MUST incluir tarefas de teste para cada regra de negócio e tarefas
  explícitas de validação e proteção para cada dado pessoal.
- Code review MUST verificar: respeito às camadas (I), presença de testes (II), validação de
  CPF/CNPJ (III) e ausência de dados sensíveis em logs (IV).
- Preferir a solução mais simples que atenda à spec (YAGNI); complexidade adicional MUST ser
  justificada no plano.

## Governance

- Esta constituição prevalece sobre quaisquer outras práticas ou convenções do projeto.
- Emendas MUST ser feitas via `/speckit-constitution`, documentadas com Sync Impact Report e
  aprovadas em revisão antes do merge.
- Versionamento semântico:
  - **MAJOR**: remoção ou redefinição incompatível de princípios ou regras de governança.
  - **MINOR**: novo princípio/seção ou expansão material de orientação existente.
  - **PATCH**: esclarecimentos, redação e correções sem mudança semântica.
- Todo PR e toda revisão MUST verificar conformidade com os princípios; não conformidades MUST
  ser corrigidas ou registradas como exceção justificada no plano da feature.
- A conformidade da constituição SHOULD ser revisada a cada nova feature relevante ou, no
  mínimo, a cada trimestre.

**Version**: 1.0.0 | **Ratified**: 2026-10-02 | **Last Amended**: 2026-10-02
