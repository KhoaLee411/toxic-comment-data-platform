import sys
from pathlib import Path
from typing import Iterator

import pandas as pd
from loguru import logger
from minio import Minio
from pyspark.sql.types import StringType, StructField, StructType
PROJECT_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PROJECT_ROOT))
from minio_config import load_minio_config
from spark_session import create_spark_session
from utils.load_config_from_file import load_cfg

CFG_FILE = "./configs/config.yml"
cfg = load_cfg(CFG_FILE)

def tokenize_partition(iterator: Iterator[pd.DataFrame]) -> Iterator[pd.DataFrame]:
    from transformers import AutoTokenizer

    local_tokenizer = AutoTokenizer.from_pretrained(cfg["model"]["name"])

    for pdf in iterator:
        encoded = local_tokenizer(
            pdf["comment_text"].tolist(),
            max_length=cfg["model"]["max_length"],
            truncation=True,
        )
        pdf["input_ids"] = [str(ids) for ids in encoded["input_ids"]]
        pdf["attention_mask"] = [str(mask) for mask in encoded["attention_mask"]]
        yield pdf.drop(columns=["comment_text"])



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
    postgres_cfg = cfg["dwh"]

    spark = create_spark_session(
        memory=spark_cfg["executor_memory"],
        extra_packages="org.postgresql:postgresql:42.7.3",
    )
    load_minio_config(spark.sparkContext, datalake_cfg)

    minio_client = Minio(
        endpoint=datalake_cfg["endpoint"],
        access_key=datalake_cfg["access_key"],
        secret_key=datalake_cfg["secret_key"],
        secure=datalake_cfg.get("secure", False),
    )

    prefix = datalake_cfg["folder_name"] + "/"
    folders = list_minio_folders(minio_client, datalake_cfg["bucket_name"], prefix)

    for folder in folders:
        logger.info(f"Processing folder: {folder}")
        parquet_path = f"s3a://{datalake_cfg['bucket_name']}/{prefix}{folder}/*.parquet"
        try:
            df = spark.read.parquet(parquet_path)
            logger.info(f"Read {df.count()} rows, columns: {df.columns}")
            
            output_schema = StructType(
                [f for f in df.schema.fields if f.name != "comment_text"]
                + [
                    StructField("input_ids", StringType(), True),
                    StructField("attention_mask", StringType(), True),
                ]
            )

            processed_df = df.mapInPandas(tokenize_partition, schema=output_schema)
            
    
            processed_df.repartition(4).write.jdbc(
                url=f"jdbc:postgresql://{postgres_cfg['host']}:{postgres_cfg['port']}/{postgres_cfg['database']}",
                table=f"{postgres_cfg['staging_schema']}.{folder}",
                mode="append",
                properties={
                    "user": postgres_cfg["user"],
                    "password": postgres_cfg["password"],
                    "driver": "org.postgresql.Driver",
                    "batchsize": "10000"
                },
            )
            logger.success(f"Successfully processed and wrote folder '{folder}' to staging.")
        except Exception as e:
            logger.error(f"Failed to process folder '{folder}': {e}")


if __name__ == "__main__":
    main()
