# Documentação Técnica

## Visão geral

Pipeline PySpark 3.5.0 para análise de pedidos e clientes de e-commerce. O código é organizado em duas camadas com responsabilidades distintas:

- **`app/src/`** — lógica de negócio: funções puras que recebem e retornam DataFrames, sem I/O
- **`app/utils/`** — infraestrutura: sessão Spark, schemas e leitura de dados

---

## Arquitetura

```
app/
├── main.py               # orquestrador do pipeline
├── src/
│   ├── data_quality.py   # DF1
│   ├── aggregation.py    # DF2
│   └── statistics.py     # DF3, DF4, DF5
└── utils/
    ├── io.py             # leitura de JSON
    ├── schemas.py        # StructType definitions
    └── session.py        # SparkSession factory
```

**Princípio central**: funções em `app/src/` não fazem I/O nem criam `SparkSession`. Recebem DataFrames como parâmetros e retornam DataFrames — testáveis de forma isolada sem dependência de arquivos ou infraestrutura.

---

## Schemas (`app/utils/schemas.py`)

```python
clients_schema = StructType([
    StructField("id",   LongType(),   nullable=False),
    StructField("name", StringType(), nullable=True),
])

pedidos_schema = StructType([
    StructField("id",        LongType(),        nullable=False),
    StructField("client_id", LongType(),        nullable=True),
    StructField("value",     DecimalType(5, 2), nullable=True),
])
```

Schemas definidos explicitamente para evitar inferência (mais lento e menos confiável em produção).

---

## Funções públicas

### `build_falhas_dq(pedidos_df, clients_df)` — `app/src/data_quality.py`

Retorna um DataFrame `(id, motivo)` com todos os pedidos que violam ao menos uma regra de qualidade.

| Parâmetro | Tipo | Descrição |
|-----------|------|-----------|
| `pedidos_df` | `DataFrame` | Pedidos brutos lidos de `data/pedidos/` |
| `clients_df` | `DataFrame` | Clientes lidos de `data/clients/` |

**Retorno**: `DataFrame` com colunas `id: LongType`, `motivo: StringType`

**Regras aplicadas (via union)**:

| Motivo | Condição |
|--------|----------|
| `"valor negativo"` | `value < 0` |
| `"id nulo"` | `id IS NULL` |
| `"valor nulo"` | `value IS NULL` |
| `"client_id inválido"` | `client_id IS NULL OR client_id = 0` |
| `"cliente não encontrado"` | `client_id` não existe em `clients_df` (left_anti com broadcast) |
| `"id duplicado"` | `id` aparece mais de uma vez em `pedidos_df` |

**Decisão de design**: padrão union em vez de `CASE WHEN` permite que um mesmo pedido apareça com múltiplos motivos independentes.

---

### `build_pedidos_por_cliente(pedidos_df, clients_df, falhas_dq)` — `app/src/aggregation.py`

Agrega pedidos válidos por cliente.

| Parâmetro | Tipo | Descrição |
|-----------|------|-----------|
| `pedidos_df` | `DataFrame` | Pedidos brutos |
| `clients_df` | `DataFrame` | Clientes (usado em broadcast join) |
| `falhas_dq` | `DataFrame` | Resultado de `build_falhas_dq` — IDs a excluir |

**Retorno**: `DataFrame` com colunas `client_id`, `name`, `qtd_pedidos: LongType`, `total_value: DecimalType(11, 2)`, ordenado por `total_value DESC`

**Notas de implementação**:
- `falhas_dq` é pré-computado e cacheado em `main.py` antes de ser passado — evita recálculo
- `clients_df` e `ids_com_falha` recebem `broadcast()` por serem pequenos (< 10 MB)
- `total_value` é cast para `DecimalType(11, 2)` para precisão monetária consistente

---

### `build_estatisticas(pedidos_por_cliente)` — `app/src/statistics.py`

Calcula estatísticas descritivas do `total_value`.

**Retorno**: `DataFrame` com uma única linha: `media`, `mediana`, `p10`, `p90`

`percentile_approx` é usado em vez de `percentile` exato — adequado para grandes volumes (não materializa todos os dados em memória).

---

### `build_acima_da_media(pedidos_por_cliente, media)` — `app/src/statistics.py`

Filtra clientes com `total_value > media`, ordenados por `total_value ASC`.

| Parâmetro | Tipo | Descrição |
|-----------|------|-----------|
| `pedidos_por_cliente` | `DataFrame` | Resultado de `build_pedidos_por_cliente` |
| `media` | `Decimal / float` | Valor extraído de `build_estatisticas().first()["media"]` |

---

### `build_media_truncada(pedidos_por_cliente, p10, p90)` — `app/src/statistics.py`

Filtra clientes com `total_value` entre P10 e P90 (inclusive), ordenados por `total_value ASC`.

---

## Pipeline (`app/main.py`)

Ordem de execução e dependências:

```
read_clients ──┐
               ├──► build_falhas_dq (DF1) ──cache──┐
read_pedidos ──┘                                    │
                                                    ├──► build_pedidos_por_cliente (DF2) ──cache──┐
               clients_df ─────────────────────────┘                                             │
                                                                                                  ├──► build_estatisticas (DF3)
                                                                                                  ├──► build_acima_da_media (DF4)
                                                                                                  └──► build_media_truncada (DF5)
```

**Uso de cache**:
- `falhas_dq.cache()` — usado por `build_pedidos_por_cliente` e depois liberado com `.unpersist()`
- `pedidos_por_cliente.cache()` — usado por DF3, DF4 e DF5; liberado após DF5

---

## Testes

### Unitários (`app/tests/`)

- Marker: `pytestmark = pytest.mark.unit`
- Dados sintéticos criados inline — nunca leem `data/`
- `SparkSession` via fixture `scope="session"` com `shuffle.partitions=2`
- Padrão de asserção: `assertDataFrameEqual(actual, expected)`

```bash
docker-compose -f infra/docker-compose.yml --profile test-unit run --rm test-unit
```

### Integração (`tests/`)

- Marker: `pytestmark = pytest.mark.integration`
- Leem dados reais de `data/` (10.001 clientes, 1.100.000 pedidos)
- Fixture `pipeline` com `scope="module"`, cache e unpersist no teardown
- Padrão de asserção: filtrar violações → `assertDataFrameEqual(violations, empty_df)`

```bash
docker-compose -f infra/docker-compose.yml --profile test-integration run --rm test-integration
```
