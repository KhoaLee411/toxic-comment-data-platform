import shutil
import sys
from pathlib import Path

import pandas as pd
from deltalake.writer import write_deltalake

sys.path.insert(0, str(Path(__file__).resolve().parent))
from load_config_from_file import load_cfg

BASE_DIR = Path(__file__).resolve().parent.parent
CFG_FILE = BASE_DIR / "configs" / "config.yml"

if __name__ == "__main__":
    cfg = load_cfg(str(CFG_FILE))
    data_cfg = cfg["data"]

    csv_dir = BASE_DIR / data_cfg["local_path"]
    delta_base = BASE_DIR / data_cfg["deltalake_folder_path"]
    delta_base.mkdir(parents=True, exist_ok=True)

    for csv_file in csv_dir.glob("*.csv"):
        file_name = csv_file.stem
        delta_path = delta_base / file_name

        if delta_path.exists():
            shutil.rmtree(delta_path)

        try:
            df = pd.read_csv(csv_file)
            write_deltalake(str(delta_path), df)
            print(f"✅ Generated Delta Lake table: {file_name}")
        except Exception as e:
            print(f"❌ Failed to process {csv_file}: {e}")