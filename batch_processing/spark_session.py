from loguru import logger
from pyspark.sql import SparkSession

_PACKAGES = ",".join([
    "io.delta:delta-spark_2.12:3.2.0",
    "org.apache.spark:spark-hadoop-cloud_2.12:3.5.1",
])


def create_spark_session(
    memory: str,
    app_name: str = "Toxic Comment Processing",
    extra_packages: str = "",
) -> SparkSession:
    try:
        logger.info(f"Initializing Spark session: {app_name}")
        packages = f"{_PACKAGES},{extra_packages}" if extra_packages else _PACKAGES

        spark = (
            SparkSession.builder.appName(app_name)
            .config("spark.executor.memory", memory)
            .config("spark.driver.memory", memory)
            .config("spark.jars.packages", packages)
            .config("spark.sql.execution.arrow.pyspark.enabled", "true")
            .config("spark.sql.extensions", "io.delta.sql.DeltaSparkSessionExtension")
            .config(
                "spark.sql.catalog.spark_catalog",
                "org.apache.spark.sql.delta.catalog.DeltaCatalog",
            )
            .getOrCreate()
        )
        logger.success("Spark session created.")
        return spark
    except Exception as e:
        logger.error(f"Failed to create Spark session: {e}")
        raise
