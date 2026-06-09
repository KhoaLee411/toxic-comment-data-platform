import shutil
import sys
from pathlib import Path

import pandas as pd
from deltalake.writer import write_deltalake
from loguru import logger

sys.path.insert(0, str(Path(__file__).resolve().parent))
from load_config_from_file import load_cfg

PROJECT_ROOT = Path(__file__).resolve().parent.parent
CFG_FILE = PROJECT_ROOT / "configs" / "config.yml"


def main():
    cfg = load_cfg(str(CFG_FILE))
    data_cfg = cfg["data"]

    csv_dir = PROJECT_ROOT / data_cfg["local_path"]
    delta_base = PROJECT_ROOT / data_cfg["deltalake_folder_path"]
    delta_base.mkdir(parents=True, exist_ok=True)

    for csv_file in sorted(csv_dir.glob("*.csv")):
        file_name = csv_file.stem.replace("-", "_")
        delta_path = delta_base / file_name

        if delta_path.exists():
            shutil.rmtree(delta_path)

        try:
            df = pd.read_csv(csv_file)
            write_deltalake(str(delta_path), df)
            logger.success(f"Generated Delta table: {file_name}")
        except Exception as e:
            logger.error(f"Failed to process '{csv_file.name}': {e}")


if __name__ == "__main__":
    main()
