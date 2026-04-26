from pyspark.sql import DataFrame
from pyspark.sql import functions as F


def build_falhas_dq(pedidos_df: DataFrame, clients_df: DataFrame) -> DataFrame:
    """Retorna pedidos com falha de qualidade (id, motivo)."""
    neg_df = (
        pedidos_df.filter(F.col("value") < 0)
        .select(F.col("id"), F.lit("valor negativo").alias("motivo"))
    )
    id_nulo_df = (
        pedidos_df.filter(F.col("id").isNull())
        .select(F.col("id"), F.lit("id nulo").alias("motivo"))
    )
    val_nulo_df = (
        pedidos_df.filter(F.col("value").isNull())
        .select(F.col("id"), F.lit("valor nulo").alias("motivo"))
    )
    cid_inv_df = (
        pedidos_df.filter(F.col("client_id").isNull() | (F.col("client_id") == 0))
        .select(F.col("id"), F.lit("client_id inválido").alias("motivo"))
    )
    orfaos_df = (
        pedidos_df
        .filter(F.col("client_id").isNotNull() & (F.col("client_id") != 0))
        .join(F.broadcast(clients_df), F.col("client_id") == clients_df["id"], "left_anti")
        .select(F.col("id"), F.lit("cliente não encontrado").alias("motivo"))
    )
    ids_dup = (
        pedidos_df.groupBy("id").count()
        .filter(F.col("count") > 1)
        .select("id")
    )
    dup_df = (
        pedidos_df.join(F.broadcast(ids_dup), on="id", how="inner")
        .select(F.col("id"), F.lit("id duplicado").alias("motivo"))
    )
    return (
        neg_df
        .union(id_nulo_df)
        .union(val_nulo_df)
        .union(cid_inv_df)
        .union(orfaos_df)
        .union(dup_df)
    )
