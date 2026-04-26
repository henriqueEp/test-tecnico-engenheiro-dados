---
description: "Revisa código PySpark em app/src/ verificando performance, qualidade e boas práticas"
agent: agent
---

Revise todos os arquivos em [app/src/](../../app/src/) verificando:

## 1. Performance

- Joins sem `broadcast()` em DataFrames pequenos (< 10 MB)
- DataFrames reutilizados múltiplas vezes sem `.cache()`
- `.cache()` usado sem `.unpersist()` correspondente
- Shuffles desnecessários (ex: `orderBy` antes de agregações)
- `spark.sql.shuffle.partitions` não configurado para o volume esperado

## 2. Qualidade de dados

- Edge cases não cobertos (nulos em colunas não validadas, valores extremos)
- Tipos incompatíveis entre schema e operações (ex: soma em `StringType`)
- Colunas monetárias fora de `DecimalType(11, 2)`

## 3. Testes

- Funções públicas em `app/src/` sem cobertura em [app/tests/](../../app/tests/)
- Testes usando `assert df.collect() == ...` em vez de `assertDataFrameEqual`
- Testes unitários lendo arquivos de `data/` (violação de isolamento)

## 4. Boas práticas

- I/O (leitura/escrita) dentro de funções em `app/src/` (deve ficar em `utils/io.py`)
- Type hints ausentes em funções públicas
- Imports não utilizados

Para cada problema encontrado, indique: **arquivo**, **linha**, **problema** e **sugestão de correção**.
