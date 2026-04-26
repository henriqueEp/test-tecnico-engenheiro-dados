from app.src.aggregation import build_pedidos_por_cliente
from app.src.data_quality import build_falhas_dq
from app.src.statistics import build_acima_da_media, build_estatisticas, build_media_truncada
from app.utils.io import read_clients, read_pedidos
from app.utils.session import get_spark


def main() -> None:
    spark = get_spark()
    spark.sparkContext.setLogLevel("ERROR")

    clients_df = read_clients(spark)
    pedidos_df = read_pedidos(spark)

    print(f"Clients : {clients_df.count():,} registros")
    print(f"Pedidos : {pedidos_df.count():,} registros")

    # DF1 — Data Quality
    falhas_dq = build_falhas_dq(pedidos_df, clients_df).cache()
    falhas_dq.show(20, truncate=False)

    # DF2 — Agregação por cliente
    pedidos_por_cliente = build_pedidos_por_cliente(pedidos_df, clients_df, falhas_dq).cache()
    pedidos_por_cliente.show(20, truncate=False)
    falhas_dq.unpersist()

    # DF3 — Estatísticas
    estatisticas = build_estatisticas(pedidos_por_cliente)
    estatisticas.show(truncate=False)
    row = estatisticas.first()

    # DF4 — Acima da média
    build_acima_da_media(pedidos_por_cliente, row["media"]).show(20, truncate=False)

    # DF5 — Média truncada
    build_media_truncada(pedidos_por_cliente, row["p10"], row["p90"]).show(20, truncate=False)
    pedidos_por_cliente.unpersist()

    spark.stop()


if __name__ == "__main__":
    main()
