# Project Guidelines

## Stack

- **PySpark 3.5.0** com Python 3.11 (incompatível com Python 3.13+)
- Sempre executar via Docker — nunca diretamente no host
- Imagem base: `jupyter/pyspark-notebook:spark-3.5.0`
- Python no container: `/opt/conda/bin/python`

## Architecture

```
app/
├── main.py               # entry point — orquestra o pipeline
├── src/                  # lógica de negócio (sem I/O)
│   ├── data_quality.py   # build_falhas_dq(pedidos_df, clients_df)
│   ├── aggregation.py    # build_pedidos_por_cliente(pedidos_df, clients_df, falhas_dq)
│   └── statistics.py     # build_estatisticas, build_acima_da_media, build_media_truncada
└── utils/                # infraestrutura (sem lógica de negócio)
    ├── io.py             # read_clients(spark), read_pedidos(spark)
    ├── schemas.py        # StructType definitions
    └── session.py        # get_spark()
tests/                    # testes de integração (dados reais de data/)
app/tests/                # testes unitários (dados sintéticos)
infra/                    # Dockerfile + docker-compose.yml (única fonte de verdade Docker)
```

## Build e Testes

```bash
# testes unitários
docker-compose -f infra/docker-compose.yml --profile test-unit run --rm test-unit

# testes de integração
docker-compose -f infra/docker-compose.yml --profile test-integration run --rm test-integration
```

## Convenções de Teste

- Testes unitários em `app/tests/` com `pytestmark = pytest.mark.unit`
- Testes de integração em `tests/` com `pytestmark = pytest.mark.integration`
- Usar `pyspark.testing.assertDataFrameEqual` — nunca `assert df.collect() == ...`
- Padrão de asserção: filtrar violações → `assertDataFrameEqual(violations, expected_empty)`
- `SparkSession` via fixture em `conftest.py` com `scope="session"`
- Dados sintéticos nos testes unitários — nunca ler `data/` em testes unitários

## Convenções PySpark

- DataFrames reutilizados múltiplas vezes devem usar `.cache()` com `.unpersist()` no teardown
- Joins com DataFrames pequenos (< 10 MB) usam `broadcast()`
- `spark.sql.shuffle.partitions=2` nos testes para evitar overhead
- Tipos monetários: `DecimalType(11, 2)`
- Funções públicas em `app/src/` recebem DataFrames como parâmetros (sem I/O interno)
