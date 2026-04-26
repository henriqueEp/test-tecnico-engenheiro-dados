# Teste Técnico — Engenheiro de Dados

Solução do teste técnico para análise de pedidos e clientes de e-commerce com PySpark 3.5.

## Pré-requisitos

- [Docker](https://docs.docker.com/get-docker/)
- [Docker Compose](https://docs.docker.com/compose/install/)

## Como executar

### 1. Clone o repositório

```bash
git clone <url-do-repositorio>
cd test-tecnico-engenheiro-dados
```

### 2. Suba o ambiente

```bash
docker-compose up --build
```

> Na primeira execução o Docker baixa a imagem `jupyter/pyspark-notebook:spark-3.5.0` (~3 GB). As execuções seguintes são imediatas.

### 3. Abra o Jupyter Lab

Acesse no navegador: **http://127.0.0.1:8888**

> Sem token ou senha.

### 4. Execute o notebook

1. Abra o arquivo `solution.ipynb`
2. No menu: **Kernel → Restart Kernel and Run All Cells**
3. Aguarde a execução completa (~2–3 min para 1M de pedidos)

### 5. Encerre o ambiente

```bash
docker-compose down
```

## Estrutura

```
.
├── data/
│   ├── clients/data.json     # ~10k clientes
│   └── pedidos/data.json     # ~1M pedidos
├── solution.ipynb            # Notebook com as 5 análises
├── Dockerfile
└── docker-compose.yml
```

## Análises implementadas

| DataFrame | Descrição |
|-----------|-----------|
| **DF1** | Data Quality — pedidos com falha (`id`, `motivo`) |
| **DF2** | Agregação por cliente — qtd. de pedidos e valor total |
| **DF3** | Estatísticas — média, mediana, P10 e P90 do valor total |
| **DF4** | Clientes com valor total acima da média |
| **DF5** | Clientes com valor total entre P10 e P90 (média truncada) |
