import logging
import sys
import traceback

from pyspark.sql import SparkSession

_PACKAGES = ",".join(
    [
        "io.delta:delta-spark_2.12:3.2.0",
        "org.apache.spark:spark-hadoop-cloud_2.12:3.5.1",
    ]
)


def create_spark_session(
    memory: str,
    app_name: str = "Toxic Comment Batch Processing",
    extra_packages: str = "",
) -> SparkSession:
    try:
        logging.info("Initializing Spark session...")
        packages = _PACKAGES if not extra_packages else f"{_PACKAGES},{extra_packages}"

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

        logging.info("Spark session created successfully.")
        return spark

    except Exception as e:
        traceback.print_exc(file=sys.stderr)
        logging.error(f"Failed to create Spark session: {e}")
        raise