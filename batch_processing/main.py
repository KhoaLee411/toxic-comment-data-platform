import sys
from pathlib import Path

from loguru import logger
from minio import Minio
from sqlalchemy import create_engine, text
from transformers import AutoTokenizer

PROJECT_ROOT = Path(__file__).resolve().parent.parent
BATCH_DIR = Path(__file__).resolve().parent
sys.path.insert(0, str(PROJECT_ROOT))
sys.path.insert(0, str(BATCH_DIR))

from minio_config import load_minio_config
from spark_session import create_spark_session
from utils.load_config_from_file import load_cfg

CFG_FILE = PROJECT_ROOT / "configs" / "config.yml"
cfg = load_cfg(str(CFG_FILE))

logger.info(f"Loading tokenizer: {cfg['model']['name']}")
tokenizer = AutoTokenizer.from_pretrained(cfg["model"]["name"])


def tokenize_batch(spark_df):
    logger.info("Converting Spark DataFrame to Pandas for tokenization...")
    pandas_df = spark_df.toPandas()
    logger.info(f"Tokenizing {len(pandas_df)} rows...")

    encoded = tokenizer(
        pandas_df["comment_text"].tolist(),
        max_length=cfg["model"]["max_length"],
        truncation=True,
    )
    pandas_df["input_ids"] = [str(ids) for ids in encoded["input_ids"]]
    pandas_df["attention_mask"] = [str(mask) for mask in encoded["attention_mask"]]
    logger.success("Tokenization complete.")
    return pandas_df.drop(columns=["comment_text"])


def _count_rows(conn, schema: str, table: str) -> int:
    try:
        result = conn.execute(text(f'SELECT COUNT(*) FROM "{schema}"."{table}"'))
        return int(result.scalar() or 0)
    except Exception as e:
        logger.warning(f"Row count failed for {schema}.{table}: {e}")
        return 0


def write_to_staging(pandas_df, table_name: str, engine, schema: str):
    with engine.begin() as conn:
        before = _count_rows(conn, schema, table_name)
    logger.info(f"Inserting {len(pandas_df)} rows into {schema}.{table_name} (currently {before} rows)...")

    pandas_df.to_sql(
        name=table_name,
        con=engine,
        schema=schema,
        if_exists="append",
        index=False,
        method="multi",
    )

    with engine.begin() as conn:
        after = _count_rows(conn, schema, table_name)
    logger.success(f"Done: {schema}.{table_name} now has {after} rows (+{after - before})")


def list_minio_folders(minio_client: Minio, bucket: str, prefix: str) -> list[str]:
    logger.info(f"Listing folders in bucket '{bucket}' under prefix '{prefix}'...")
    subfolders = set()
    for obj in minio_client.list_objects(bucket, prefix=prefix, recursive=False):
        part = obj.object_name[len(prefix):].strip("/").split("/")[0]
        if part:
            subfolders.add(part)
    folders = list(subfolders)
    logger.success(f"Found {len(folders)} folder(s): {folders}")
    return folders


def main():
    datalake_cfg = cfg["datalake"]
    spark_cfg = cfg["spark"]
    postgres_cfg = cfg["dw_postgres"]

    spark = create_spark_session(memory=spark_cfg["executor_memory"])
    load_minio_config(spark.sparkContext, datalake_cfg)

    minio_client = Minio(
        endpoint=datalake_cfg["endpoint"],
        access_key=datalake_cfg["access_key"],
        secret_key=datalake_cfg["secret_key"],
        secure=datalake_cfg.get("secure", False),
    )

    engine = create_engine(
        f"postgresql://{postgres_cfg['user']}:{postgres_cfg['password']}"
        f"@{postgres_cfg['host']}:{postgres_cfg['port']}/{postgres_cfg['database']}"
    )

    prefix = datalake_cfg["folder_name"] + "/"
    folders = list_minio_folders(minio_client, datalake_cfg["bucket_name"], prefix)

    for folder in folders:
        logger.info(f"Processing folder: {folder}")
        parquet_path = f"s3a://{datalake_cfg['bucket_name']}/{prefix}{folder}/*.parquet"
        try:
            df = spark.read.parquet(parquet_path)
            logger.info(f"Read {df.count()} rows, columns: {df.columns}")
            processed_df = tokenize_batch(df)
            write_to_staging(
                processed_df,
                table_name=folder,
                engine=engine,
                schema=postgres_cfg["staging_schema"],
            )
        except Exception as e:
            logger.error(f"Failed to process folder '{folder}': {e}")


if __name__ == "__main__":
    main()
