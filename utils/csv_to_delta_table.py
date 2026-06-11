import shutil
from pathlib import Path

import pandas as pd
from deltalake.writer import write_deltalake
from load_config_from_file import load_cfg

CFG_PATH = "./configs/config.yml"


def csv_to_delta(csv_folder: str, delta_folder: str) -> None:
    csv_dir = Path(csv_folder)
    delta_dir = Path(delta_folder)

    for csv_file in csv_dir.glob("*.csv"):
        table_name = csv_file.stem
        delta_path = delta_dir / table_name

        if delta_path.exists():
            shutil.rmtree(delta_path)

        try:
            df = pd.read_csv(csv_file)
            write_deltalake(str(delta_path), df)
            print(f"✅ Converted '{csv_file.name}' -> Delta table '{table_name}'")
        except Exception as e:
            print(f"❌ Failed to convert '{csv_file.name}': {e}")


if __name__ == "__main__":
    cfg = load_cfg(CFG_PATH)
    csv_to_delta(cfg["data"]["csv_path"], cfg["data"]["delta_path"])