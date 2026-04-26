from pyspark.sql import DataFrame
from pyspark.sql import functions as F
from pyspark.sql.types import DecimalType


def build_pedidos_por_cliente(
    pedidos_df: DataFrame,
    clients_df: DataFrame,
    falhas_dq: DataFrame,
) -> DataFrame:
    """Agrega pedidos válidos por cliente, ordenado por total_value desc."""
    ids_com_falha = falhas_dq.select("id").filter(F.col("id").isNotNull()).distinct()

    pedidos_validos = (
        pedidos_df
        .filter(F.col("id").isNotNull())
        .join(F.broadcast(ids_com_falha), on="id", how="left_anti")
    )

    return (
        pedidos_validos.alias("p")
        .join(F.broadcast(clients_df.alias("c")), F.col("p.client_id") == F.col("c.id"), "inner")
        .groupBy(F.col("c.id").alias("client_id"), F.col("c.name").alias("name"))
        .agg(
            F.count("*").alias("qtd_pedidos"),
            F.sum(F.col("p.value")).cast(DecimalType(11, 2)).alias("total_value"),
        )
        .orderBy(F.col("total_value").desc())
    )
