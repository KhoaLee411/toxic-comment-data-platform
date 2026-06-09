import json
import sys
from pathlib import Path

from loguru import logger
from pyspark.sql import DataFrame
from pyspark.sql.functions import col, from_json, udf
from pyspark.sql.types import StringType, StructField, StructType
from transformers import AutoTokenizer

PROJECT_ROOT = Path(__file__).resolve().parent.parent
BATCH_DIR = PROJECT_ROOT / "batch_processing"
sys.path.insert(0, str(PROJECT_ROOT))
sys.path.insert(0, str(BATCH_DIR))

from spark_session import create_spark_session
from utils.load_config_from_file import load_cfg

CFG_FILE = PROJECT_ROOT / "configs" / "config.yml"
cfg = load_cfg(str(CFG_FILE))

logger.info(f"Loading tokenizer: {cfg['model']['name']}")
tokenizer = AutoTokenizer.from_pretrained(cfg["model"]["name"])

# Debezium CDC payload schema — only "after" fields needed
_AFTER_SCHEMA = StructType([
    StructField("comment_text", StringType(), True),
    StructField("labels", StringType(), True),
])

_PAYLOAD_SCHEMA = StructType([
    StructField("op", StringType(), True),
    StructField("after", _AFTER_SCHEMA, True),
])


@udf(
    returnType=StructType([
        StructField("input_ids", StringType(), False),
        StructField("attention_mask", StringType(), False),
    ])
)
def hf_tokenize(text: str):
    if not text:
        text = ""
    enc = tokenizer(text, max_length=cfg["model"]["max_length"], truncation=True)
    return {
        "input_ids": json.dumps(enc["input_ids"]),
        "attention_mask": json.dumps(enc["attention_mask"]),
    }


def write_to_production(batch_df: DataFrame, batch_id: int, postgres_cfg: dict):
    inserts = batch_df.filter(col("op") == "c")
    if inserts.rdd.isEmpty():
        return

    tok = (
        inserts.select(
            col("after.labels").cast("long").alias("labels"),
            col("after.comment_text").alias("comment_text"),
        )
        .withColumn("tok", hf_tokenize(col("comment_text")))
        .select(
            col("labels"),
            col("tok.input_ids").alias("input_ids"),
            col("tok.attention_mask").alias("attention_mask"),
        )
    )

    tok = tok.cache()
    row_count = tok.count()
    tok.write.jdbc(
        url=(
            f"jdbc:postgresql://{postgres_cfg['host']}:{postgres_cfg['port']}"
            f"/{postgres_cfg['database']}"
        ),
        table="production.comments",
        mode="append",
        properties={
            "user": postgres_cfg["user"],
            "password": postgres_cfg["password"],
            "driver": "org.postgresql.Driver",
        },
    )
    tok.unpersist()
    logger.success(f"Batch {batch_id}: wrote {row_count} rows to production.comments")


def main():
    stream_cfg = cfg["stream"]
    spark_cfg = cfg["spark"]
    postgres_cfg = cfg["dw_postgres"]

    spark = create_spark_session(
        memory=spark_cfg["executor_memory"],
        app_name="Toxic Comment Stream Processing",
        extra_packages="org.apache.spark:spark-sql-kafka-0-10_2.12:3.5.1",
    )

    kafka_df = (
        spark.readStream.format("kafka")
        .option("kafka.bootstrap.servers", stream_cfg["kafka_bootstrap_servers"])
        .option("subscribe", stream_cfg["topic"])
        .option("startingOffsets", "earliest")
        .load()
    )

    parsed = kafka_df.select(
        from_json(col("value").cast("string"), _PAYLOAD_SCHEMA).alias("payload")
    ).select(
        col("payload.op").alias("op"),
        col("payload.after").alias("after"),
    )

    logger.info(f"Consuming from Kafka topic: {stream_cfg['topic']}")
    logger.info("Waiting for events (Ctrl+C to stop)...")

    query = (
        parsed.writeStream
        .foreachBatch(lambda df, bid: write_to_production(df, bid, postgres_cfg))
        .option(
            "checkpointLocation",
            str(PROJECT_ROOT / "data_local" / "stream_checkpoint"),
        )
        .start()
    )
    query.awaitTermination()


if __name__ == "__main__":
    main()
