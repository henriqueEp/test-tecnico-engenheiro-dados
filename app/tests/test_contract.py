import logging
from decimal import Decimal
from pathlib import Path

import pytest
from pyspark.sql.types import DecimalType, LongType, StringType, StructField, StructType

from app.utils.contract import validate_contract

pytestmark = pytest.mark.unit

# ── Schemas sintéticos ────────────────────────────────────────────────────────

_clients_schema = StructType([
    StructField("id",   LongType(),   nullable=False),
    StructField("name", StringType(), nullable=True),
])

_pedidos_schema = StructType([
    StructField("id",        LongType(),        nullable=True),
    StructField("client_id", LongType(),        nullable=True),
    StructField("value",     DecimalType(5, 2), nullable=True),
])

# ── Fixtures de contrato YAML ─────────────────────────────────────────────────


@pytest.fixture()
def clients_contract(tmp_path: Path) -> Path:
    contract = tmp_path / "clients.yaml"
    contract.write_text(
        """
apiVersion: v3.0.0
kind: DataContract
id: urn:test:clients
name: clients
schema:
  - name: clients
    columns:
      - name: id
        logicalType: long
        isNullable: false
      - name: name
        logicalType: string
        isNullable: true
quality:
  - column: id
    rule: not_null
""",
        encoding="utf-8",
    )
    return contract


@pytest.fixture()
def pedidos_contract(tmp_path: Path) -> Path:
    contract = tmp_path / "pedidos.yaml"
    contract.write_text(
        """
apiVersion: v3.0.0
kind: DataContract
id: urn:test:pedidos
name: pedidos
schema:
  - name: pedidos
    columns:
      - name: id
        logicalType: long
        isNullable: true
      - name: client_id
        logicalType: long
        isNullable: true
      - name: value
        logicalType: "decimal(5,2)"
        isNullable: true
quality:
  - column: value
    rule: positive
""",
        encoding="utf-8",
    )
    return contract


# ── Testes de schema (hard stop) ──────────────────────────────────────────────


def test_schema_valido_nao_levanta(spark, clients_contract):
    df = spark.createDataFrame([(1, "Alice")], _clients_schema)
    validate_contract(df, clients_contract)  # não deve lançar


def test_schema_coluna_ausente_levanta_value_error(spark, tmp_path):
    contract = tmp_path / "missing_col.yaml"
    contract.write_text(
        """
apiVersion: v3.0.0
kind: DataContract
id: urn:test:missing
name: missing
schema:
  - name: t
    columns:
      - name: id
        logicalType: long
        isNullable: true
      - name: coluna_inexistente
        logicalType: string
        isNullable: true
""",
        encoding="utf-8",
    )
    df = spark.createDataFrame([(1,)], StructType([StructField("id", LongType(), nullable=True)]))
    with pytest.raises(ValueError, match="coluna ausente: 'coluna_inexistente'"):
        validate_contract(df, contract)


def test_schema_tipo_errado_levanta_value_error(spark, tmp_path):
    contract = tmp_path / "wrong_type.yaml"
    contract.write_text(
        """
apiVersion: v3.0.0
kind: DataContract
id: urn:test:wrongtype
name: wrongtype
schema:
  - name: t
    columns:
      - name: id
        logicalType: string
        isNullable: true
""",
        encoding="utf-8",
    )
    # DF tem id como LongType, contrato espera string
    df = spark.createDataFrame([(1,)], StructType([StructField("id", LongType(), nullable=True)]))
    with pytest.raises(ValueError, match="tipo incorreto em 'id'"):
        validate_contract(df, contract)


# ── Testes de quality rules (soft warning) ────────────────────────────────────


def test_not_null_sem_violacao_nao_emite_warning(spark, clients_contract, caplog):
    df = spark.createDataFrame([(1, "Alice"), (2, "Bob")], _clients_schema)
    with caplog.at_level(logging.WARNING, logger="contract"):
        validate_contract(df, clients_contract)
    assert not any("not_null violado" in m for m in caplog.messages)


def test_not_null_com_violacao_emite_warning(spark, tmp_path, caplog):
    contract = tmp_path / "nullable_id.yaml"
    contract.write_text(
        """
apiVersion: v3.0.0
kind: DataContract
id: urn:test:nullable
name: nullable
schema:
  - name: t
    columns:
      - name: id
        logicalType: long
        isNullable: true
quality:
  - column: id
    rule: not_null
""",
        encoding="utf-8",
    )
    schema = StructType([StructField("id", LongType(), nullable=True)])
    df = spark.createDataFrame([(1,), (None,)], schema)
    with caplog.at_level(logging.WARNING, logger="contract"):
        validate_contract(df, contract)  # não deve lançar
    assert any("not_null violado" in m for m in caplog.messages)


def test_positive_com_valor_negativo_emite_warning(spark, pedidos_contract, caplog):
    df = spark.createDataFrame(
        [(1, 10, Decimal("50.00")), (2, 10, Decimal("-5.00"))],
        _pedidos_schema,
    )
    with caplog.at_level(logging.WARNING, logger="contract"):
        validate_contract(df, pedidos_contract)  # não deve lançar
    assert any("positive violado" in m for m in caplog.messages)


def test_positive_sem_violacao_nao_emite_warning(spark, pedidos_contract, caplog):
    df = spark.createDataFrame(
        [(1, 10, Decimal("50.00")), (2, 20, Decimal("30.00"))],
        _pedidos_schema,
    )
    with caplog.at_level(logging.WARNING, logger="contract"):
        validate_contract(df, pedidos_contract)
    assert not any("positive violado" in m for m in caplog.messages)
