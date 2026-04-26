# Teste Técnico — Engenheiro de Dados


![CI](https://github.com/henriqueEp/test-tecnico-engenheiro-dados/actions/workflows/ci.yml/badge.svg)
![Python](https://img.shields.io/badge/python-3.11-blue)
![PySpark](https://img.shields.io/badge/pyspark-3.5.0-orange)
![Docker](https://img.shields.io/badge/docker-compose%20v2-2496ED)

Solução do teste técnico para análise de pedidos e clientes de e-commerce com PySpark 3.5.

Duas abordagens disponíveis: **notebook** (foco em leitura e apresentação) e **projeto Python** (estrutura pronta para esteira de CI/CD).

---

## Abordagem 1 — Notebook (Jupyter + Docker)

### Pré-requisitos

- [Docker](https://docs.docker.com/get-docker/)
- [Docker Compose](https://docs.docker.com/compose/install/)

### Como executar

#### 1. Clone o repositório

```bash
git clone <url-do-repositorio>
cd test-tecnico-engenheiro-dados
```

#### 2. Suba o ambiente

```bash
docker-compose -f infra/docker-compose.yml up jupyter --build
```

> Na primeira execução o Docker baixa a imagem `jupyter/pyspark-notebook:spark-3.5.0` (~3 GB). As execuções seguintes são imediatas.

#### 3. Abra o Jupyter Lab

Acesse no navegador: **http://127.0.0.1:8888**

> Sem token ou senha.

#### 4. Execute o notebook

1. Abra o arquivo `solution.ipynb`
2. No menu: **Kernel → Restart Kernel and Run All Cells**
3. Aguarde a execução completa (~2–3 min para 1M de pedidos)

#### 5. Encerre o ambiente

```bash
docker-compose -f infra/docker-compose.yml down
```

---

## Abordagem 2 — Projeto Python (estrutura produtiva)

### Pré-requisitos

- [Docker](https://docs.docker.com/get-docker/) e [Docker Compose](https://docs.docker.com/compose/install/)

> PySpark 3.5.0 requer Python 3.11. O Docker já traz o ambiente correto — nenhuma instalação adicional necessária.

### Como executar

#### 1. Clone o repositório

```bash
git clone <url-do-repositorio>
cd test-tecnico-engenheiro-dados
```

### Estrutura

```
app/
├── main.py               # entry point
├── src/                  # lógica de negócio (transformações PySpark puras)
│   ├── data_quality.py   # DF1 — falhas_dq
│   ├── aggregation.py    # DF2 — pedidos_por_cliente
│   └── statistics.py     # DF3, DF4, DF5
├── utils/                # infraestrutura (sem lógica de negócio)
│   ├── io.py             # leitura de dados
│   ├── schemas.py        # StructType definitions
│   └── session.py        # SparkSession
└── tests/                # testes unitários
tests/                    # testes de integração (esteira)
infra/
├── Dockerfile
└── docker-compose.yml
.github/
├── copilot-instructions.md   # contexto automático para GitHub Copilot
├── prompts/                  # prompts reutilizáveis (/code-review, /write-tests, /check-patterns, /debug-cicd)
├── agents/                   # agentes especializados (refactor, docs-writer)
├── skills/                   # skills on-demand (test-data-factory)
└── workflows/ci.yml          # CI/CD (lint → unit → integration → build/push → run)
docs/
├── technical.md              # arquitetura, schemas, assinaturas de funções, pipeline
└── business.md               # DF1–DF5 em linguagem de negócio
```

### Executar a aplicação

```bash
# build
docker-compose -f infra/docker-compose.yml --profile app build app

# rodar
docker-compose -f infra/docker-compose.yml --profile app run --rm app
```

### Executar testes

```bash
# build
docker-compose -f infra/docker-compose.yml --profile test-unit build test-unit
docker-compose -f infra/docker-compose.yml --profile test-integration build test-integration

# testes unitários (sem dados reais, rápido)
docker-compose -f infra/docker-compose.yml --profile test-unit run --rm test-unit

# testes de integração (com dados reais)
docker-compose -f infra/docker-compose.yml --profile test-integration run --rm test-integration
```

---

## CI/CD

O workflow `.github/workflows/ci.yml` simula uma esteira de dados completa com 5 estágios em sequência:

```
lint ──► unit-tests ──► integration-tests ──► build-and-push ──► run-pipeline
```

| Estágio | Trigger | O que faz |
|---------|---------|-----------|
| **Lint** | PRs e push | `ruff check app/` — verifica erros, imports não usados e ordenação de imports |
| **Unit Tests** | Após lint (paralelo) | Roda `pytest -m unit` dentro do container Docker |
| **Integration Tests** | Após lint (paralelo) | Roda `pytest -m integration` com dados reais (`data/`) montados |
| **Build & Push** | Push em `main` + aprovação | Aguarda gate `production` → builda e faz push para **GitHub Container Registry** (`ghcr.io`) |
| **Run Pipeline** | Após build + aprovação | Executa `app/main.py` — simula o disparo do job em produção |

> Os estágios 4 e 5 só rodam em push direto para `main` e exigem aprovação manual via **Environment `production`** (Settings → Environments → Required reviewers). Sem a configuração do environment, os jobs disparam automaticamente.

---

## Análises implementadas

| DataFrame | Descrição |
|-----------|-----------|
| **DF1** | Data Quality — pedidos com falha (`id`, `motivo`) |
| **DF2** | Agregação por cliente — qtd. de pedidos e valor total |
| **DF3** | Estatísticas — média, mediana, P10 e P90 do valor total |
| **DF4** | Clientes com valor total acima da média |
| **DF5** | Clientes com valor total entre P10 e P90 (média truncada) |

---

## Uso de IA no projeto

Este projeto foi desenvolvido com suporte a GitHub Copilot, com customizações em `.github/` que demonstram diferentes primitivos da plataforma:

### `copilot-instructions.md` — instruções automáticas

**Arquivo**: `.github/copilot-instructions.md`  
**Invocação**: automática — ativo em toda sessão do Copilot neste repositório

Contexto permanente injetado automaticamente em toda sessão do Copilot no repositório. Contém: stack, arquitetura, convenções de teste e padrões PySpark. Qualquer dev que clonar o repo recebe o contexto sem configuração adicional.

### Prompts (`/code-review`, `/write-tests`, `/check-patterns`)

**Arquivos**: `.github/prompts/`  
**Invocação**: digite `/` no chat do Copilot e selecione o prompt desejado

Tarefas reutilizáveis invocadas sob demanda via `/` no chat:

| Prompt | Mode | Arquivo | Descrição |
|--------|------|---------|-----------|
| `/code-review` | `agent` | `prompts/code-review.prompt.md` | Revisa `app/src/` — performance, DQ, testes, boas práticas |
| `/write-tests` | `agent` | `prompts/write-tests.prompt.md` | Gera testes seguindo os padrões do projeto (`assertDataFrameEqual`, markers, fixtures) |
| `/check-patterns` | `ask` | `prompts/check-patterns.prompt.md` | Avalia conformidade arquitetural — **somente leitura**, retorna tabela de status |

O modo `ask` em `/check-patterns` é intencional: um prompt de auditoria não deve editar arquivos.

### Agent `refactor` — ferramenta restrita

**Arquivo**: `.github/agents/refactor.agent.md`  
**Invocação**: selecione o agente **refactor** no seletor de agentes do Copilot Chat

Agente especializado em refatoração com `tools: [read, edit, search]` — sem acesso a terminal e sem capacidade de criar novos arquivos. Garante que refatorações se limitem a melhorar código existente sem alterar a estrutura do projeto.

### Agent `docs-writer` — documentação técnica e de negócio

**Arquivo**: `.github/agents/docs-writer.agent.md`  
**Invocação**: selecione o agente **docs-writer** no seletor de agentes e passe `technical`, `business` ou `both` como argumento

Agente especializado em gerar documentação em `docs/`. Lê `app/src/`, `app/main.py` e os testes antes de escrever — nunca executa código. Separa a linguagem técnica (assinaturas, schemas, pipeline) da linguagem de negócio (o que cada DataFrame representa para o produto).

### Skill `test-data-factory` — geração de massas de teste

**Arquivo**: `.github/skills/test-data-factory/SKILL.md`  
**Invocação**: referencie `#test-data-factory` no chat ou peça explicitamente _"use a skill test-data-factory para..."_

Skill on-demand para gerar dados sintéticos em testes unitários PySpark. Empacota: checklist de edge cases por tipo de coluna, templates dos schemas do projeto, regras de `DecimalType`/`LongType` e padrões de `assertDataFrameEqual`. Evita repetição de boilerplate ao criar novos testes em `app/tests/`.

### Prompt `/debug-cicd` — diagnóstico de falhas na esteira

**Arquivo**: `.github/prompts/debug-cicd.prompt.md`  
**Invocação**: digite `/debug-cicd` no chat e cole o log de erro do GitHub Actions como argumento

Prompt especializado em diagnosticar falhas no pipeline CI/CD. Lê automaticamente o `ci.yml` e o `docker-compose.yml` antes de analisar e retorna: causa raiz, estágio afetado, correção exata e como verificar o fix. Inclui base de conhecimento das armadilhas conhecidas do projeto (`docker-compose` vs `docker compose`, `No module named pyspark`, `Python worker failed to connect`, etc.).

### Resumo dos primitivos

| Primitivo | Arquivo | Como invocar |
|-----------|---------|--------------|
| Instructions | `.github/copilot-instructions.md` | Automático |
| Prompt `/code-review` | `.github/prompts/code-review.prompt.md` | `/code-review` no chat |
| Prompt `/write-tests` | `.github/prompts/write-tests.prompt.md` | `/write-tests` no chat |
| Prompt `/check-patterns` | `.github/prompts/check-patterns.prompt.md` | `/check-patterns` no chat |
| Prompt `/debug-cicd` | `.github/prompts/debug-cicd.prompt.md` | `/debug-cicd` no chat |
| Agent `refactor` | `.github/agents/refactor.agent.md` | Seletor de agentes → **refactor** |
| Agent `docs-writer` | `.github/agents/docs-writer.agent.md` | Seletor de agentes → **docs-writer** |
| Skill `test-data-factory` | `.github/skills/test-data-factory/SKILL.md` | `#test-data-factory` no chat |

---

## Documentação

| Arquivo | Conteúdo |
|---------|----------|
| [docs/technical.md](docs/technical.md) | Arquitetura, schemas, assinaturas de funções, grafo de dependências do pipeline, convenções de teste |
| [docs/business.md](docs/business.md) | DF1–DF5 em linguagem não técnica, critérios de negócio e uso esperado de cada resultado |
