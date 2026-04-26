from pyspark.sql import DataFrame
from pyspark.sql import functions as F


def build_estatisticas(pedidos_por_cliente: DataFrame) -> DataFrame:
    """Retorna média, mediana, P10 e P90 do total_value por cliente."""
    return pedidos_por_cliente.select(
        F.mean("total_value").alias("media"),
        F.percentile_approx("total_value", 0.5).alias("mediana"),
        F.percentile_approx("total_value", 0.1).alias("p10"),
        F.percentile_approx("total_value", 0.9).alias("p90"),
    )


def build_acima_da_media(pedidos_por_cliente: DataFrame, media) -> DataFrame:
    """Clientes com total_value acima da média, ordenados por valor crescente."""
    return (
        pedidos_por_cliente
        .filter(F.col("total_value") > media)
        .orderBy("total_value")
    )


def build_media_truncada(pedidos_por_cliente: DataFrame, p10, p90) -> DataFrame:
    """Clientes com total_value entre P10 e P90, ordenados por valor crescente."""
    return (
        pedidos_por_cliente
        .filter((F.col("total_value") >= p10) & (F.col("total_value") <= p90))
        .orderBy("total_value")
    )
