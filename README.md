# Projeto de Aprendizado — Spec Kit: Cadastro de Cliente

Este guia descreve o fluxo completo do [Spec Kit](https://github.com/github/spec-kit) aplicado a um exemplo prático: um módulo de **cadastro de cliente**. Use este README como roteiro para aprender a ferramenta do início ao fim.

## 1. Instalar o CLI `specify`

```bash
uv tool install specify-cli --from git+https://github.com/github/spec-kit.git
```

## 2. Criar e inicializar o projeto

```bash
specify init cadastro-cliente --integration claude
cd cadastro-cliente
```

Isso cria a estrutura do projeto e instala os comandos slash (`/speckit.*`) para o seu agente (neste caso, Claude Code).

## 3. `/speckit.constitution` — definir os princípios do projeto

Exemplo de prompt:

> Este projeto segue Clean Architecture, testes automatizados obrigatórios para regras de negócio, e todo dado pessoal (CPF/CNPJ) deve ser validado e armazenado seguindo boas práticas de segurança (sem log de dados sensíveis em texto claro).

Isso fica registrado e vale para todas as features seguintes do projeto.

## 4. `/speckit.specify` — descrever o *o quê* e *por quê*

Exemplo de prompt:

> Quero um módulo de cadastro de cliente: criar, listar, editar e remover clientes. Cada cliente tem nome, CPF ou CNPJ (não pode repetir), e-mail, telefone e endereço. O sistema deve impedir cadastro duplicado pelo mesmo CPF/CNPJ e validar e-mail.

O Spec Kit gera a spec formal (requisitos, user stories, critérios de aceite) sem ainda falar de stack técnica.

## 5. `/speckit.clarify` — fechar ambiguidades

O agente vai perguntar coisas que ficaram abertas na spec, por exemplo:

- CPF e CNPJ serão tratados como o mesmo campo ou campos separados?
- O endereço é obrigatório?
- Existe paginação na listagem?

Você responde e a spec é refinada.

## 6. `/speckit.plan` — entrar com stack e arquitetura

Exemplo de prompt:

> Backend em Python com FastAPI, banco PostgreSQL, ORM SQLAlchemy, validação com Pydantic, testes com pytest.

Gera o plano técnico: camadas, modelos, endpoints, migrations etc.

## 7. `/speckit.tasks` — quebrar em tarefas executáveis

Gera uma lista de tasks, por exemplo:

- Criar model `Cliente`
- Criar migration
- Implementar validação de CPF/CNPJ único
- Criar endpoints REST
- Escrever testes de cada endpoint

## 8. `/speckit.analyze` (opcional, recomendado) — checar consistência

Confere se spec, plano e tasks estão alinhados antes de gerar código — útil para pegar lacunas, como uma regra da spec que não ficou coberta por nenhuma task.

## 9. `/speckit.implement` — gerar o código

O agente executa as tasks em sequência e escreve de fato o código do módulo de cadastro de cliente.

## 10. `/speckit.converge` (opcional, iterativo)

Depois de implementado, roda para verificar se sobrou algo divergente entre o que foi pedido e o que foi codado, adicionando novas tasks se necessário — útil ao incrementar o projeto (ex: pedir um campo novo mais tarde).

## Referências

- [Instalação do Spec Kit](https://github.com/github/spec-kit)
- [Guia de instalação oficial](https://github.github.com/spec-kit/installation.html)
- [Guia de upgrade](https://github.com/github/spec-kit/blob/main/docs/upgrade.md)
## Rodando o módulo (feature 001-cadastro-cliente)

O código gerado pelo `/speckit.implement` está em `src/cadastro_cliente/` (Clean Architecture:
`domain` → `application` → `interfaces/api` / `infrastructure`) e os testes em `tests/`.

```bash
uv sync
uv run pytest            # unitários + integração/contrato (PostgreSQL via Docker/testcontainers)
```

Setup completo, variáveis de ambiente (chaves de criptografia) e cenários de validação manual:
[specs/001-cadastro-cliente/quickstart.md](specs/001-cadastro-cliente/quickstart.md).
