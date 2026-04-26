---
description: "Gera testes unitários ou de integração para funções PySpark seguindo os padrões do projeto"
agent: agent
argument-hint: "Função ou módulo alvo (ex: build_falhas_dq, statistics)"
---

Gere testes para a função ou módulo indicado, seguindo **estritamente** os padrões deste projeto.

## Regras obrigatórias

### Localização
- **Testes unitários** → `app/tests/test_<módulo>.py`
- **Testes de integração** → `tests/test_integration.py`

### Marker obrigatório (primeira linha após imports)
```python
# unitário
pytestmark = pytest.mark.unit

# integração
pytestmark = pytest.mark.integration
```

### SparkSession
- Sempre via fixture de `conftest.py` com `scope="session"`
- Nunca criar `SparkSession` diretamente no teste
- Nos testes unitários: `spark.conf.set("spark.sql.shuffle.partitions", "2")`

### Padrão de asserção
```python
from pyspark.testing import assertDataFrameEqual

# CORRETO — filtrar violações e assert que está vazio
violations = result.filter(condicao_invalida)
assertDataFrameEqual(violations, spark.createDataFrame([], violations.schema))

# ERRADO — nunca usar
assert result.collect() == [...]
```

### Dados sintéticos (unitários)
- Criar dados inline no teste — nunca ler `data/`
- Cobrir: caso feliz, valor nulo, valor inválido, edge case

### Cache (integração)
- Fixtures com `scope="module"` devem usar `.cache()` e `.unpersist()` no teardown

## Estrutura esperada

Leia os arquivos existentes em [app/tests/](../../app/tests/) e [tests/](../../tests/) para seguir o padrão já estabelecido antes de gerar novos testes.
