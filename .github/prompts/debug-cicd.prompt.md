---
description: "Diagnostica falhas no pipeline CI/CD do GitHub Actions — use quando um job falhar ou a esteira travar"
argument-hint: "Cole aqui o log de erro do GitHub Actions"
agent: agent
tools: [read, search]
---

Você é um especialista em GitHub Actions e Docker. Analise o log de erro abaixo e identifique a causa raiz da falha no pipeline CI/CD deste projeto.

## Contexto do projeto

Leia os arquivos relevantes antes de responder:

- [ci.yml](.github/workflows/ci.yml) — definição do pipeline (5 estágios: lint → unit-tests → integration-tests → build-and-push → run-pipeline)
- [infra/docker-compose.yml](infra/docker-compose.yml) — serviços Docker usados nos testes
- [infra/Dockerfile](infra/Dockerfile) — imagem base do projeto

## Stack

- PySpark 3.5.0 com Python 3.11 (incompatível com 3.13+)
- Imagem base: `jupyter/pyspark-notebook:spark-3.5.0`
- Docker Compose V2 (`docker compose`, sem hífen)
- Runner: `ubuntu-latest`

## Armadilhas conhecidas

- `docker-compose: command not found` → usar `docker compose` (V2, sem hífen)
- `No module named 'pyspark'` → o container não está usando o Python correto; verificar `PYSPARK_PYTHON` e `PYSPARK_DRIVER_PYTHON`
- `Python worker failed to connect` → PySpark tentando usar o Python do host em vez do container
- `Accept timed out` → o worker Python não subiu; geralmente causado por `python` não encontrado no PATH
- Estágios 4 e 5 não rodam em PRs → comportamento esperado (`if: github.ref == 'refs/heads/main'`)
- Environment `production` requer aprovação manual antes de build/push/run

## Sua resposta deve conter

1. **Causa raiz** — qual linha ou configuração causou o erro
2. **Estágio afetado** — em qual dos 5 estágios ocorreu
3. **Correção** — mudança exata de arquivo/linha para resolver
4. **Como verificar** — como confirmar que o fix funcionou

## Log de erro

$input
