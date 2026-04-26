---
name: test-data-factory
description: 'Gera massas de dados sintéticos para testes unitários PySpark. Use quando precisar criar novos testes em app/tests/ — a skill cobre edge cases, schemas e boilerplate do projeto.'
---

# Test Data Factory

## Quando usar esta skill

Ao criar ou ampliar testes unitários em `app/tests/`. A skill garante cobertura de edge cases e conformidade com os schemas do projeto.

---

## Schemas do projeto

Sempre use estes schemas inline nos testes — nunca importe de `app/utils/schemas`.

```python
from pyspark.sql.types import DecimalType, LongType, StringType, StructField, StructType

_pedidos_schema = StructType([
    StructField("id",        LongType(),        nullable=True),
    StructField("client_id", LongType(),        nullable=True),
    StructField("value",     DecimalType(5, 2), nullable=True),
])

_clients_schema = StructType([
    StructField("id",   LongType(),   nullable=False),
    StructField("name", StringType(), nullable=True),
])
```

> `DecimalType(5, 2)` nos dados de entrada. Casts para `DecimalType(11, 2)` acontecem na agregação — não nos dados brutos.

---

## Checklist de edge cases por função

### `build_falhas_dq`

| Caso | Como criar o dado |
|------|-------------------|
| Valor negativo | `value = Decimal("-10.00")` |
| Valor nulo | `value = None` |
| ID nulo | `id = None` (nullable=True no schema de teste) |
| client_id nulo | `client_id = None` |
| client_id zero | `client_id = 0` |
| Órfão (client não existe) | `client_id` com valor que não existe em `clients_df` |
| ID duplicado | dois registros com mesmo `id` |
| Pedido válido (não aparece) | `id` único, `client_id` válido, `value > 0` |

### `build_pedidos_por_cliente`

| Caso | Como criar o dado |
|------|-------------------|
| Pedido com falha excluído | incluir um `id` em `falhas_dq`, verificar que não aparece no resultado |
| Ordenação DESC por total | dois clientes com totais distintos → verificar ordem com `checkRowOrder=True` |
| Múltiplos pedidos por cliente | mesmo `client_id` em N linhas → verificar `qtd_pedidos` e `total_value` |

### `build_estatisticas` / `build_acima_da_media` / `build_media_truncada`

| Caso | Como criar o dado |
|------|-------------------|
| Média calculada corretamente | 3+ clientes com totais conhecidos → `float(row["media"]) == pytest.approx(...)` |
| Acima da média | clientes com total acima e abaixo → filtrar e verificar quem sobra |
| Dentro de P10–P90 | conjunto pequeno onde o intervalo é conhecido — use 5+ clientes |

---

## Padrão de asserção

```python
# Resultado esperado vazio (padrão para validação negativa)
assertDataFrameEqual(actual, spark.createDataFrame([], actual.schema))

# Resultado com dados esperados
expected = spark.createDataFrame([...], actual.schema)
assertDataFrameEqual(actual, expected)

# Verificar ordem
assertDataFrameEqual(actual, expected, checkRowOrder=True)
```

Nunca use `assert df.collect() == [...]`.

---

## Template de arquivo de teste

```python
from decimal import Decimal

import pytest
from pyspark.sql.types import DecimalType, LongType, StringType, StructField, StructType
from pyspark.testing import assertDataFrameEqual

from app.src.<modulo> import <funcao>

pytestmark = pytest.mark.unit

_pedidos_schema = StructType([...])
_clients_schema = StructType([...])


def test_<caso>(spark):
    pedidos = spark.createDataFrame([(<id>, <client_id>, Decimal("<value>"))], _pedidos_schema)
    clients = spark.createDataFrame([(<id>, "<name>")], _clients_schema)

    actual = <funcao>(pedidos, clients)
    expected = spark.createDataFrame([...], actual.schema)
    assertDataFrameEqual(actual, expected)
```

---

## Regras de geração

1. **IDs começam em 1** — IDs 0 são inválidos por regra de negócio (`client_id = 0` é rejeitado pelo DQ)
2. **Valores monetários com `Decimal("X.XX")`** — nunca `float` (imprecisão de ponto flutuante)
3. **Dados mínimos por teste** — use o menor conjunto que demonstra o comportamento. Evite datasets grandes em testes unitários
4. **Um comportamento por teste** — não valide múltiplas regras no mesmo `test_*`
5. **`clients_df` sempre contém o `client_id` dos pedidos válidos** — a menos que o teste seja sobre clientes não encontrados
