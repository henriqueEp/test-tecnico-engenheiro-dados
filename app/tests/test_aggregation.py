from decimal import Decimal

import pytest
from pyspark.sql.types import DecimalType, LongType, StringType, StructField, StructType
from pyspark.testing import assertDataFrameEqual

from app.src.aggregation import build_pedidos_por_cliente
from app.src.data_quality import build_falhas_dq

pytestmark = pytest.mark.unit

_pedidos_schema = StructType([
    StructField("id",        LongType(),        nullable=True),
    StructField("client_id", LongType(),        nullable=True),
    StructField("value",     DecimalType(5, 2), nullable=True),
])

_clients_schema = StructType([
    StructField("id",   LongType(),   nullable=False),
    StructField("name", StringType(), nullable=True),
])


def test_agregacao_basica(spark):
    pedidos = spark.createDataFrame(
        [(1, 1, Decimal("10.00")), (2, 1, Decimal("20.00")), (3, 2, Decimal("5.00"))],
        _pedidos_schema,
    )
    clients = spark.createDataFrame([(1, "Alice"), (2, "Bob")], _clients_schema)
    falhas = build_falhas_dq(pedidos, clients)

    actual = build_pedidos_por_cliente(pedidos, clients, falhas)
    expected = spark.createDataFrame(
        [(1, "Alice", 2, Decimal("30.00")), (2, "Bob", 1, Decimal("5.00"))],
        actual.schema,
    )
    assertDataFrameEqual(actual, expected, checkRowOrder=True)


def test_pedidos_invalidos_excluidos(spark):
    pedidos = spark.createDataFrame(
        [(1, 1, Decimal("-5.00")), (2, 1, Decimal("10.00"))],
        _pedidos_schema,
    )
    clients = spark.createDataFrame([(1, "Alice")], _clients_schema)
    falhas = build_falhas_dq(pedidos, clients)

    actual = build_pedidos_por_cliente(pedidos, clients, falhas)
    expected = spark.createDataFrame(
        [(1, "Alice", 1, Decimal("10.00"))],
        actual.schema,
    )
    assertDataFrameEqual(actual, expected)


def test_ordenado_por_total_desc(spark):
    pedidos = spark.createDataFrame(
        [(1, 1, Decimal("10.00")), (2, 2, Decimal("100.00")), (3, 3, Decimal("50.00"))],
        _pedidos_schema,
    )
    clients = spark.createDataFrame([(1, "A"), (2, "B"), (3, "C")], _clients_schema)
    falhas = build_falhas_dq(pedidos, clients)

    actual = build_pedidos_por_cliente(pedidos, clients, falhas)
    expected = spark.createDataFrame(
        [(2, "B", 1, Decimal("100.00")), (3, "C", 1, Decimal("50.00")), (1, "A", 1, Decimal("10.00"))],
        actual.schema,
    )
    assertDataFrameEqual(actual, expected, checkRowOrder=True)
