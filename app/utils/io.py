import os
from pathlib import Path

from pyspark.sql import DataFrame, SparkSession

from app.utils.contract import validate_contract
from app.utils.schemas import clients_schema, pedidos_schema

_CONTRACTS_DIR = Path(__file__).parent.parent / "contracts"


def get_data_dir() -> str:
    return "/home/jovyan/data" if os.path.exists("/home/jovyan/data") else "data"


def read_clients(spark: SparkSession, data_dir: str | None = None) -> DataFrame:
    if data_dir is None:
        data_dir = get_data_dir()
    df = spark.read.schema(clients_schema).json(f"{data_dir}/clients/data.json")
    validate_contract(df, _CONTRACTS_DIR / "clients.yaml")
    return df


def read_pedidos(spark: SparkSession, data_dir: str | None = None) -> DataFrame:
    if data_dir is None:
        data_dir = get_data_dir()
    df = spark.read.schema(pedidos_schema).json(f"{data_dir}/pedidos/data.json")
    validate_contract(df, _CONTRACTS_DIR / "pedidos.yaml")
    return df
