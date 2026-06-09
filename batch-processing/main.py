import sys
from pathlib import Path

PROJ_ROOT = Path(__file__).resolve().parent.parent
BATCH_DIR = Path(__file__).resolve().parent
sys.path.insert(0, str(PROJ_ROOT))
sys.path.insert(0, str(BATCH_DIR))

from loguru import logger
from minio import Minio
from minio_config import load_minio_config
from spark_session import create_spark_session
from sqlalchemy import create_engine, text
from transformers import AutoTokenizer

from utils.load_config_from_file import load_cfg

CFG_FILE = PROJ_ROOT / "configs" / "config.yml"

logger.info("Loading application configurations...")
cfg = load_cfg(str(CFG_FILE))
datalake_cfg = cfg["datalake"]
spark_cfg = cfg["spark"]
postgres_cfg = cfg["dw_postgres"]
model_cfg = cfg["model"]

logger.info(f"Loading tokenizer: {model_cfg['name']}")
tokenizer = AutoTokenizer.from_pretrained(model_cfg["name"])


def tokenize_dataframe(spark_df):
    """Convert Spark DataFrame to Pandas and tokenize comment_text."""
    logger.info("Converting Spark DataFrame to Pandas...")
    pandas_df = spark_df.toPandas()

    logger.info("Tokenizing comment_text...")
    tokenized = tokenizer(
        pandas_df["comment_text"].tolist(),
        max_length=model_cfg["max_length"],
        truncation=True,
    )

    pandas_df["input_ids"] = [str(ids) for ids in tokenized["input_ids"]]
    pandas_df["attention_mask"] = [str(mask) for mask in tokenized["attention_mask"]]
    logger.success("Tokenization complete.")
    return pandas_df.drop(columns=["comment_text"])


def count_rows(conn, schema: str, table: str) -> int:
    try:
        result = conn.execute(text(f'SELECT COUNT(*) FROM "{schema}"."{table}"'))
        return int(result.scalar() or 0)
    except Exception as e:
        logger.warning(f"Count failed for {schema}.{table}: {e}")
        return 0


def load_to_staging(pandas_df, table_name: str):
    """Write processed DataFrame to the PostgreSQL staging schema."""
    staging_schema = postgres_cfg["staging_schema"]
    engine = create_engine(
        f"postgresql://{postgres_cfg['user']}:{postgres_cfg['password']}"
        f"@{postgres_cfg['host']}:{postgres_cfg['port']}/{postgres_cfg['database']}"
    )

    with engine.begin() as conn:
        before = count_rows(conn, staging_schema, table_name)
        logger.info(f"Before insert: {staging_schema}.{table_name} has {before} rows")

    logger.info(f"Inserting {len(pandas_df)} rows into {staging_schema}.{table_name}...")
    pandas_df.to_sql(
        name=table_name,
        con=engine,
        schema=staging_schema,
        if_exists="append",
        index=False,
        method="multi",
    )

    with engine.begin() as conn:
        after = count_rows(conn, staging_schema, table_name)
        logger.success(
            f"After insert: {staging_schema}.{table_name} has {after} rows "
            f"(inserted {after - before})"
        )


def list_dataset_folders(minio_client, bucket: str, prefix: str) -> list[str]:
    """Return immediate subfolder names under the given MinIO prefix."""
    logger.info(f"Listing folders in bucket '{bucket}' under prefix '{prefix}'...")
    subfolders = set()
    for obj in minio_client.list_objects(bucket, prefix=prefix, recursive=False):
        part = obj.object_name[len(prefix):].strip("/").split("/")[0]
        if part:
            subfolders.add(part)
    folders = list(subfolders)
    logger.success(f"Found folders: {folders}")
    return folders


if __name__ == "__main__":
    spark = create_spark_session(memory=spark_cfg["executor_memory"])
    load_minio_config(spark.sparkContext, datalake_cfg)

    minio_client = Minio(
        endpoint=datalake_cfg["endpoint"],
        access_key=datalake_cfg["access_key"],
        secret_key=datalake_cfg["secret_key"],
        secure=datalake_cfg.get("secure", False),
    )

    prefix = datalake_cfg["folder_name"] + "/"
    folders = list_dataset_folders(minio_client, datalake_cfg["bucket_name"], prefix)

    for folder in folders:
        logger.info(f"Processing folder: {folder}")
        parquet_path = f"s3a://{datalake_cfg['bucket_name']}/{prefix}{folder}/*.parquet"

        df = spark.read.parquet(parquet_path)
        logger.info(f"Rows: {df.count()}, Columns: {df.columns}")

        processed_df = tokenize_dataframe(df)
        logger.info(f"Processed shape: {processed_df.shape}, Columns: {list(processed_df.columns)}")

        load_to_staging(processed_df, table_name=folder)