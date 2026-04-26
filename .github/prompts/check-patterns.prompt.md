---
description: "Avalia se o projeto segue os padrões arquiteturais e convenções definidos — apenas leitura, sem edições"
agent: ask
---

Analise o projeto e verifique se os padrões definidos em [.github/copilot-instructions.md](../copilot-instructions.md) estão sendo seguidos.

## Checklist de verificação

### Arquitetura
- [ ] `app/src/` contém apenas lógica de negócio: `data_quality.py`, `aggregation.py`, `statistics.py` (sem I/O, sem schemas, sem sessão)
- [ ] `app/utils/` contém apenas infraestrutura: `io.py`, `schemas.py`, `session.py`
- [ ] `app/utils/io.py` é o único ponto de leitura de dados
- [ ] `app/utils/session.py` é o único lugar onde `SparkSession` é criada
- [ ] `app/utils/schemas.py` é o único lugar onde `StructType` são definidos
- [ ] `app/main.py` é o único orquestrador do pipeline
- [ ] Imports em `app/main.py` seguem a ordem: `app.src.*` → `app.utils.*`
- [ ] Nenhum arquivo em `app/src/` faz import de `app.utils.io` ou cria `SparkSession`

### Testes unitários (`app/tests/`)
- [ ] Todos os arquivos têm `pytestmark = pytest.mark.unit`
- [ ] Nenhum teste lê arquivos de `data/`
- [ ] Todos usam `assertDataFrameEqual` (nenhum `assert df.collect() == ...`)
- [ ] `conftest.py` tem fixture com `scope="session"` e `shuffle.partitions=2`

### Testes de integração (`tests/`)
- [ ] Todos os arquivos têm `pytestmark = pytest.mark.integration`
- [ ] Fixtures de escopo `module` usam `.cache()` + `.unpersist()`
- [ ] Testes usam padrão "filtrar violações → assert vazio"

### PySpark
- [ ] Todos os joins com DataFrames pequenos usam `broadcast()` (incluindo `ids_dup` e `ids_com_falha`)
- [ ] DataFrames reutilizados usam `.cache()`
- [ ] Colunas monetárias são `DecimalType(11, 2)`

### Docker
- [ ] `infra/` é a única fonte de verdade Docker (sem Dockerfile ou docker-compose na raiz)
- [ ] Serviços de teste separados: `test-unit` e `test-integration`

Apresente os resultados como uma tabela com: **item**, **status** (✅/❌/⚠️) e **observação**.
