from loguru import logger
from pyspark import SparkContext


def _normalize_endpoint(endpoint: str, secure: bool) -> str:
    if endpoint.startswith(("http://", "https://")):
        return endpoint
    return f"{'https' if secure else 'http'}://{endpoint}"


def load_minio_config(spark_context: SparkContext, datalake_cfg: dict):
    try:
        logger.info("Applying MinIO configuration to Spark...")
        hadoop_conf = spark_context._jsc.hadoopConfiguration()
        secure = bool(datalake_cfg.get("secure", False))
        endpoint = _normalize_endpoint(datalake_cfg["endpoint"], secure)

        hadoop_conf.set("fs.s3a.access.key", datalake_cfg["access_key"])
        hadoop_conf.set("fs.s3a.secret.key", datalake_cfg["secret_key"])
        hadoop_conf.set("fs.s3a.endpoint", endpoint)
        hadoop_conf.set(
            "fs.s3a.aws.credentials.provider",
            "org.apache.hadoop.fs.s3a.SimpleAWSCredentialsProvider",
        )
        hadoop_conf.set("fs.s3a.path.style.access", "true")
        hadoop_conf.set("fs.s3a.connection.ssl.enabled", "true" if secure else "false")
        hadoop_conf.set("fs.s3a.impl", "org.apache.hadoop.fs.s3a.S3AFileSystem")
        logger.success("MinIO configuration applied.")
    except Exception as e:
        logger.error(f"Failed to configure MinIO: {e}")
        raise
