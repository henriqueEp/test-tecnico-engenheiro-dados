import pytest
from pyspark.sql import Window
from pyspark.sql import functions as F
from pyspark.testing import assertDataFrameEqual

from app.src.aggregation import build_pedidos_por_cliente
from app.src.data_quality import build_falhas_dq
from app.src.statistics import build_acima_da_media, build_estatisticas, build_media_truncada
from app.utils.io import read_clients, read_pedidos

pytestmark = pytest.mark.integration


@pytest.fixture(scope="module")
def pipeline(spark):
    clients = read_clients(spark)
    pedidos = read_pedidos(spark)
    falhas = build_falhas_dq(pedidos, clients).cache()
    agg = build_pedidos_por_cliente(pedidos, clients, falhas).cache()
    stats_row = build_estatisticas(agg).first()

    yield {
        "clients": clients,
        "pedidos": pedidos,
        "falhas_dq": falhas,
        "pedidos_por_cliente": agg,
        "stats": stats_row,
    }

    falhas.unpersist()
    agg.unpersist()


def test_volume_clients(pipeline):
    assert pipeline["clients"].count() == 10_001


def test_volume_pedidos(pipeline):
    assert pipeline["pedidos"].count() == 1_100_000


def test_falhas_dq_colunas(pipeline):
    assert pipeline["falhas_dq"].columns == ["id", "motivo"]


def test_falhas_dq_motivos_esperados(spark, pipeline):
    # Verifica que os motivos obrigatórios existem via left_anti join —
    # se algum faltar, ele aparece no resultado (que deve ser vazio)
    motivos_distintos = pipeline["falhas_dq"].select("motivo").distinct()
    motivos_obrigatorios = spark.createDataFrame(
        [("valor negativo",), ("valor nulo",), ("client_id inválido",), ("id duplicado",)],
        motivos_distintos.schema,
    )
    ausentes = motivos_obrigatorios.join(motivos_distintos, on="motivo", how="left_anti")
    assertDataFrameEqual(ausentes, spark.createDataFrame([], motivos_distintos.schema))


def test_pedidos_por_cliente_ordenado_desc(spark, pipeline):
    # Detecta violações de ordem via window — qualquer linha onde
    # total_value > linha anterior indica que a ordenação está errada
    w = Window.orderBy(F.monotonically_increasing_id())
    violations = (
        pipeline["pedidos_por_cliente"]
        .limit(100)
        .withColumn("prev_val", F.lag("total_value").over(w))
        .filter(F.col("prev_val").isNotNull() & (F.col("total_value") > F.col("prev_val")))
        .drop("prev_val")
    )
    assertDataFrameEqual(violations, spark.createDataFrame([], violations.schema))


def test_acima_da_media_todos_acima(spark, pipeline):
    result = build_acima_da_media(pipeline["pedidos_por_cliente"], pipeline["stats"]["media"])
    fora_da_media = result.filter(F.col("total_value") <= pipeline["stats"]["media"])
    assertDataFrameEqual(fora_da_media, spark.createDataFrame([], result.schema))


def test_media_truncada_dentro_percentis(spark, pipeline):
    result = build_media_truncada(
        pipeline["pedidos_por_cliente"],
        pipeline["stats"]["p10"],
        pipeline["stats"]["p90"],
    )
    fora_dos_percentis = result.filter(
        (F.col("total_value") < pipeline["stats"]["p10"])
        | (F.col("total_value") > pipeline["stats"]["p90"])
    )
    assertDataFrameEqual(fora_dos_percentis, spark.createDataFrame([], result.schema))
