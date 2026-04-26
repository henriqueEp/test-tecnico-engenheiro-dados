from decimal import Decimal

import pytest
from pyspark.sql import functions as F
from pyspark.sql.types import DecimalType, LongType, StringType, StructField, StructType
from pyspark.testing import assertDataFrameEqual

from app.src.statistics import build_acima_da_media, build_estatisticas, build_media_truncada

pytestmark = pytest.mark.unit

_schema = StructType([
    StructField("client_id",   LongType(),         nullable=False),
    StructField("name",        StringType(),        nullable=True),
    StructField("qtd_pedidos", LongType(),          nullable=False),
    StructField("total_value", DecimalType(11, 2),  nullable=True),
])


@pytest.fixture
def sample_df(spark):
    return spark.createDataFrame(
        [
            (1, "A", 5, Decimal("100.00")),
            (2, "B", 3, Decimal("200.00")),
            (3, "C", 7, Decimal("300.00")),
            (4, "D", 4, Decimal("400.00")),
            (5, "E", 6, Decimal("500.00")),
        ],
        _schema,
    )


def test_media(sample_df):
    row = build_estatisticas(sample_df).first()
    assert float(row["media"]) == 300.0


def test_acima_da_media(spark, sample_df):
    row = build_estatisticas(sample_df).first()
    actual = build_acima_da_media(sample_df, row["media"])
    expected = spark.createDataFrame(
        [(4, "D", 4, Decimal("400.00")), (5, "E", 6, Decimal("500.00"))],
        actual.schema,
    )
    assertDataFrameEqual(actual, expected, checkRowOrder=True)


def test_media_truncada_dentro_dos_bounds(spark, sample_df):
    row = build_estatisticas(sample_df).first()
    actual = build_media_truncada(sample_df, row["p10"], row["p90"])
    fora_dos_limites = actual.filter(
        (F.col("total_value") < row["p10"]) | (F.col("total_value") > row["p90"])
    )
    assertDataFrameEqual(fora_dos_limites, spark.createDataFrame([], actual.schema))
