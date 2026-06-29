import json
import sys
from pathlib import Path

from loguru import logger
from pyflink.common import Row
from pyflink.table import DataTypes, EnvironmentSettings, TableEnvironment
from pyflink.table.expressions import call, col
from pyflink.table.udf import udf
from transformers import AutoTokenizer

PROJECT_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

from utils.load_config_from_file import load_cfg

CFG_FILE = PROJECT_ROOT / "configs" / "config.yml"
cfg = load_cfg(str(CFG_FILE))

stream_cfg = cfg["stream"]
postgres_cfg = cfg["dwh"]

JARS_PATH = str(PROJECT_ROOT / "jars")

logger.info(f"Loading tokenizer for model: {cfg['model']['name']}")
tokenizer = AutoTokenizer.from_pretrained(cfg["model"]["name"])

@udf(
    result_type=DataTypes.ROW(
        [
            DataTypes.FIELD("input_ids", DataTypes.STRING()),
            DataTypes.FIELD("attention_mask", DataTypes.STRING()),
        ]
    )
)
def hf_tokenize(text: str):
    if text is None:
        text = ""
    enc = tokenizer(text, max_length=cfg["model"]["max_length"], truncation=True)
    return Row(
        input_ids=json.dumps(enc["input_ids"], ensure_ascii=False),
        attention_mask=json.dumps(enc["attention_mask"], ensure_ascii=False),
    )

def main():
    logger.info("Initializing PyFlink Table Environment...")
    t_env = TableEnvironment.create(
        environment_settings=EnvironmentSettings.in_streaming_mode()
    )

    t_env.get_config().set(
        "pipeline.jars",
        f"file://{JARS_PATH}/flink-sql-connector-kafka-3.2.0-1.18.jar;"
        + f"file://{JARS_PATH}/flink-sql-avro-confluent-registry-1.18.0.jar;"
        + f"file://{JARS_PATH}/flink-avro-1.18.0.jar;"
        + f"file://{JARS_PATH}/flink-connector-jdbc-3.2.0-1.18.jar;"
        + f"file://{JARS_PATH}/postgresql-42.7.7.jar",
    )

    # Đăng ký UDF
    t_env.create_temporary_system_function("hf_tokenize", hf_tokenize)

    # ---- Kafka source (Debezium Avro) ----
    logger.info(f"Connecting to Kafka topic: {stream_cfg['topic']} with Avro format")
    t_env.execute_sql(
        f"""
        CREATE TABLE m2_streaming_src (
        comment_text STRING,
        labels BIGINT
        ) WITH (
        'connector' = 'kafka',
        'topic' = '{stream_cfg['topic']}',
        'properties.bootstrap.servers' = '{stream_cfg['kafka_bootstrap_servers']}',
        'properties.group.id' = 'flink-staging-consumer-001',
        'scan.startup.mode' = 'earliest-offset',
        'value.format' = 'debezium-avro-confluent',
        'value.debezium-avro-confluent.schema-registry.url' = 'http://localhost:8081'
        )
    """
    )

    # ---- JDBC sink ----
    jdbc_url = f"jdbc:postgresql://{postgres_cfg['host']}:{postgres_cfg['port']}/{postgres_cfg['database']}"
    target_table = "staging.streaming"
    
    logger.info(f"Configuring JDBC Sink: {jdbc_url} -> {target_table}")
    t_env.execute_sql(
        f"""
        CREATE TABLE staging_streaming_sink (
          id STRING NOT NULL,
          labels BIGINT,
          input_ids STRING,
          attention_mask STRING,
          PRIMARY KEY (id) NOT ENFORCED
        ) WITH (
          'connector' = 'jdbc',
          'url' = '{jdbc_url}',
          'table-name' = '{target_table}',
          'username' = '{postgres_cfg['user']}',
          'password' = '{postgres_cfg['password']}',
          'driver' = 'org.postgresql.Driver'
        )
    """
    )

    src = t_env.from_path("m2_streaming_src")
    logger.info("Source schema:")
    src.print_schema()

    tok = src.select(
        call("uuid").alias("id"),
        col("labels"),
        hf_tokenize(col("comment_text")).alias("tok"),
    ).select(
        col("id"),
        col("labels"),
        col("tok").get("input_ids").alias("input_ids"),
        col("tok").get("attention_mask").alias("attention_mask"),
    )

    # Execute continuous insert
    logger.info("Waiting for the job (Ctrl+C to stop)...")
    tok.execute_insert("staging_streaming_sink").wait()


if __name__ == "__main__":
    main()
