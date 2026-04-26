from decimal import Decimal

import pytest
from pyspark.sql.types import DecimalType, LongType, StringType, StructField, StructType
from pyspark.testing import assertDataFrameEqual

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


def test_valor_negativo(spark):
    pedidos = spark.createDataFrame([(1, 1, Decimal("-10.00"))], _pedidos_schema)
    clients = spark.createDataFrame([(1, "Alice")], _clients_schema)

    actual = build_falhas_dq(pedidos, clients)
    expected = spark.createDataFrame([(1, "valor negativo")], actual.schema)
    assertDataFrameEqual(actual, expected)


def test_valor_nulo(spark):
    pedidos = spark.createDataFrame([(1, 1, None)], _pedidos_schema)
    clients = spark.createDataFrame([(1, "Alice")], _clients_schema)

    actual = build_falhas_dq(pedidos, clients)
    expected = spark.createDataFrame([(1, "valor nulo")], actual.schema)
    assertDataFrameEqual(actual, expected)


def test_client_id_invalido(spark):
    pedidos = spark.createDataFrame(
        [(1, None, Decimal("5.00")), (2, 0, Decimal("5.00"))],
        _pedidos_schema,
    )
    clients = spark.createDataFrame([(3, "Alice")], _clients_schema)

    actual = build_falhas_dq(pedidos, clients)
    expected = spark.createDataFrame(
        [(1, "client_id inválido"), (2, "client_id inválido")],
        actual.schema,
    )
    assertDataFrameEqual(actual, expected)


def test_id_duplicado(spark):
    pedidos = spark.createDataFrame(
        [(1, 1, Decimal("5.00")), (1, 2, Decimal("3.00"))],
        _pedidos_schema,
    )
    clients = spark.createDataFrame([(1, "Alice"), (2, "Bob")], _clients_schema)

    actual = build_falhas_dq(pedidos, clients)
    expected = spark.createDataFrame(
        [(1, "id duplicado"), (1, "id duplicado")],
        actual.schema,
    )
    assertDataFrameEqual(actual, expected)


def test_pedido_valido_nao_incluso(spark):
    pedidos = spark.createDataFrame([(1, 1, Decimal("5.00"))], _pedidos_schema)
    clients = spark.createDataFrame([(1, "Alice")], _clients_schema)

    actual = build_falhas_dq(pedidos, clients)
    expected = spark.createDataFrame([], actual.schema)
    assertDataFrameEqual(actual, expected)
