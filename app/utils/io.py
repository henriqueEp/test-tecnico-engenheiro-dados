import os

from pyspark.sql import DataFrame, SparkSession

from app.utils.schemas import clients_schema, pedidos_schema


def get_data_dir() -> str:
    return "/home/jovyan/data" if os.path.exists("/home/jovyan/data") else "data"


def read_clients(spark: SparkSession, data_dir: str | None = None) -> DataFrame:
    if data_dir is None:
        data_dir = get_data_dir()
    return spark.read.schema(clients_schema).json(f"{data_dir}/clients/data.json")


def read_pedidos(spark: SparkSession, data_dir: str | None = None) -> DataFrame:
    if data_dir is None:
        data_dir = get_data_dir()
    return spark.read.schema(pedidos_schema).json(f"{data_dir}/pedidos/data.json")
