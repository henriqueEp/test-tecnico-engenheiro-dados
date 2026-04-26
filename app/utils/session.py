from pyspark.sql import SparkSession


def get_spark(app_name: str = "teste-tecnico") -> SparkSession:
    return (
        SparkSession.builder
        .appName(app_name)
        .master("local[*]")
        .getOrCreate()
    )
