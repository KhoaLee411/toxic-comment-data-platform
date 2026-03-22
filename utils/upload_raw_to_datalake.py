import os
from pathlib import Path

from load_config_from_file import load_cfg
from minio import Minio

CFG_FILE = "./configs/config.yml"


def upload_data_local_to_minio(minio_client, raw_path, bucket_name, folder_name):
    local_path = Path(raw_path)

    for local_file in local_path.rglob("*"):
        if local_file.is_file():
            remote_path = os.path.join(
                folder_name, str(local_file.relative_to(local_path))
            )
              
            minio_client.fput_object(bucket_name, remote_path, str(local_file))
            print(f"📤 Uploaded {local_file} → {bucket_name}/{remote_path}")


def main():
    cfg = load_cfg(CFG_FILE)
    data_lake_cfg = cfg["data_lake"]
    raw_path = cfg["raw"]

    minio_client = Minio(
        endpoint=data_lake_cfg["endpoint"],
        access_key=data_lake_cfg["access_key"],
        secret_key=data_lake_cfg["secret_key"],
        secure=data_lake_cfg.get("secure", False),
    )

    if not minio_client.bucket_exists(data_lake_cfg["bucket_name"]):
        minio_client.make_bucket(data_lake_cfg["bucket_name"])
        print(f"✅ Created bucket: {data_lake_cfg['bucket_name']}")
    else:
        print(f"ℹ️ Bucket {data_lake_cfg['bucket_name']} already exists")

    upload_data_local_to_minio(
        minio_client,
        raw_path,
        data_lake_cfg["bucket_name"],
        data_lake_cfg["folder_bronze"],
    )


if __name__ == "__main__":
    main()
