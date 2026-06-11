import json
from pathlib import Path

from deltalake import DeltaTable
from load_config_from_file import load_cfg

CFG_FILE = "./configs/config.yml"


def investigate(table_name: str, path: Path):
    print(f"\n===== {table_name} =====")
    dt = DeltaTable(path / table_name, version=0)
    print("Schema:", json.loads(dt.schema().to_json()))
    print("Version:", dt.version())
    print("Files:", dt.file_uris())
    print("Sample data:\n", dt.to_pandas(columns=["comment_text", "labels"]))
    print("History:\n", dt.history())


def main():
    data_cfg = load_cfg(CFG_FILE)["data"]
    base_path = Path(data_cfg["delta_path"])

    for table_name in ["text_comment_1", "text_comment_2"]:
        investigate(table_name, base_path)


if __name__ == "__main__":
    main()