from pyspark.sql.types import DecimalType, LongType, StringType, StructField, StructType

clients_schema = StructType([
    StructField("id",   LongType(),   nullable=False),
    StructField("name", StringType(), nullable=True),
])

pedidos_schema = StructType([
    StructField("id",        LongType(),        nullable=False),
    StructField("client_id", LongType(),        nullable=True),
    StructField("value",     DecimalType(5, 2), nullable=True),
])
