import time

from app.src.aggregation import build_pedidos_por_cliente
from app.src.data_quality import build_falhas_dq
from app.src.statistics import build_acima_da_media, build_estatisticas, build_media_truncada
from app.utils.io import read_clients, read_pedidos
from app.utils.logger import get_logger
from app.utils.session import get_spark

log = get_logger("pipeline")


def main() -> None:
    spark = get_spark()
    spark.sparkContext.setLogLevel("ERROR")
    t0 = time.time()

    log.info("Iniciando...")

    clients_df = read_clients(spark)
    pedidos_df = read_pedidos(spark)
    log.info(f"Clientes lidos  : {clients_df.count():>10,}")
    log.info(f"Pedidos lidos   : {pedidos_df.count():>10,}")

    # DF1 — Data Quality
    falhas_dq = build_falhas_dq(pedidos_df, clients_df).cache()
    log.info(f"[DF1] falhas_dq           : {falhas_dq.count():>10,} registros rejeitados")
    falhas_dq.show(20, truncate=False)

    # DF2 — Agregação por cliente
    pedidos_por_cliente = build_pedidos_por_cliente(pedidos_df, clients_df, falhas_dq).cache()
    log.info(f"[DF2] pedidos_por_cliente : {pedidos_por_cliente.count():>10,} clientes com pedidos válidos")
    pedidos_por_cliente.show(20, truncate=False)
    falhas_dq.unpersist()

    # DF3 — Estatísticas
    estatisticas = build_estatisticas(pedidos_por_cliente)
    estatisticas.show(truncate=False)
    row = estatisticas.first()
    log.info(f"[DF3] média={row['media']:.2f}  mediana={row['mediana']:.2f}  P10={row['p10']:.2f}  P90={row['p90']:.2f}")

    # DF4 — Acima da média
    acima = build_acima_da_media(pedidos_por_cliente, row["media"]).cache()
    log.info(f"[DF4] acima_da_media      : {acima.count():>10,} clientes acima da média")
    acima.show(20, truncate=False)
    acima.unpersist()

    # DF5 — Média truncada
    truncada = build_media_truncada(pedidos_por_cliente, row["p10"], row["p90"]).cache()
    log.info(f"[DF5] media_truncada      : {truncada.count():>10,} clientes entre P10 e P90")
    truncada.show(20, truncate=False)
    truncada.unpersist()
    pedidos_por_cliente.unpersist()

    log.info(f"Concluído em {time.time() - t0:.1f}s")

    spark.stop()


if __name__ == "__main__":
    main()