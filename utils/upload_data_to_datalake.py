import sys
from pathlib import Path

from loguru import logger
from minio import Minio

sys.path.insert(0, str(Path(__file__).resolve().parent))
from load_config_from_file import load_cfg

PROJECT_ROOT = Path(__file__).resolve().parent.parent
CFG_FILE = PROJECT_ROOT / "configs" / "config.yml"


def upload_directory_to_minio(
    minio_client: Minio, local_path: Path, bucket_name: str, minio_prefix: str
):
    local_path = Path(local_path)
    for local_file in local_path.rglob("*"):
        if local_file.is_file():
            remote_path = f"{minio_prefix}/{local_file.relative_to(local_path)}"
            minio_client.fput_object(bucket_name, remote_path, str(local_file))
            logger.info(f"Uploaded {local_file.name} → {bucket_name}/{remote_path}")


def main():
    cfg = load_cfg(str(CFG_FILE))
    datalake_cfg = cfg["datalake"]
    data_cfg = cfg["data"]

    minio_client = Minio(
        endpoint=datalake_cfg["endpoint"],
        access_key=datalake_cfg["access_key"],
        secret_key=datalake_cfg["secret_key"],
        secure=datalake_cfg.get("secure", False),
    )

    bucket = datalake_cfg["bucket_name"]
    if not minio_client.bucket_exists(bucket):
        minio_client.make_bucket(bucket)
        logger.success(f"Created bucket: {bucket}")
    else:
        logger.info(f"Bucket '{bucket}' already exists")

    upload_directory_to_minio(
        minio_client,
        local_path=PROJECT_ROOT / data_cfg["deltalake_folder_path"],
        bucket_name=bucket,
        minio_prefix=datalake_cfg["folder_name"],
    )
    logger.success("Upload complete.")


if __name__ == "__main__":
    main()
