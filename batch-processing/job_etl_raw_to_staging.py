# Logic chính của pipeline ETL từ raw đến staging
from spark_session import create_spark_session
from utils.load_config_from_file import load_cfg
from storage_utils import load_minio_config
from minio import Minio
from loguru import logger

CFG_FILE = "./configs/config.yml"

def list_sub_folders(minio_client, bucket_name, prefix):
    """
    Returns: List of subfolder names.
    """
    logger.info(f"Listing sub folders in bucket '{bucket_name}' with prefix '{prefix}'...")
    sub_folders = set()
    objects = minio_client.list_objects(bucket_name, prefix=prefix, recursive=False)

    for obj in objects:
        parts = obj.object_name[len(prefix) :].strip("/").split("/")
        if parts and parts[0]:
            sub_folders.add(parts[0])

    folders = list(sub_folders)
    logger.success(f"Found sub folders: {folders}")
    return folders

if __name__ == "__main__":

    cfg = load_cfg(CFG_FILE)
    executor_memory = cfg["spark"]["executor_memory"]
    data_lake_cfg = cfg["data_lake"]

    spark = create_spark_session(memory=executor_memory)

    load_minio_config(spark.sparkContext, data_lake_cfg)

    minio_client = Minio(
        endpoint=data_lake_cfg["endpoint"],
        access_key=data_lake_cfg["access_key"],
        secret_key=data_lake_cfg["secret_key"],
        secure=data_lake_cfg.get("secure", False),
        )
    
    # List sub folders in the bronze folder
    prefix = data_lake_cfg["folder_bronze"] + "/"
    folders = list_sub_folders(minio_client, data_lake_cfg["bucket_name"], prefix)
    
    for folder in folders:
        logger.info(f"Processing folder: {folder}")

        parquet_path = f"s3a://{data_lake_cfg['bucket_name']}/{prefix}{folder}/*.parquet"
        json_path = f"s3a://{data_lake_cfg['bucket_name']}/{prefix}{folder}/*.json"

        df = spark.read.parquet(parquet_path)

        logger.info("=== Spark DataFrame (before processing) ===")
        logger.info(f"Shape (rows x cols) ≈ ({df.count()} x {len(df.columns)})")
        logger.info(f"Columns: {df.columns}")

        pandas_df_final = processing_dataframe(df)

        logger.info("=== Pandas DataFrame (after processing) ===")
        logger.info(f"Shape: {pandas_df_final.shape}")
        logger.info(f"Columns: {list(pandas_df_final.columns)}")

        load_to_staging_table(pandas_df_final, table_name=folder)


