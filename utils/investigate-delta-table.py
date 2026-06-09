
import json
import sys
from pathlib import Path

from deltalake import DeltaTable

sys.path.insert(0, str(Path(__file__).resolve().parent))
from load_config_from_file import load_cfg

BASE_DIR = Path(__file__).resolve().parent.parent
CFG_FILE = BASE_DIR / "configs" / "config.yml"


def inspect_table(delta_path: Path):
    print("=" * 60)
    print(f"Table: {delta_path.name}")
    dt = DeltaTable(str(delta_path))
    print(f"Version      : {dt.version()}")
    print(f"Schema       : {json.loads(dt.schema().to_json())}")
    print(f"Files        : {dt.file_uris()}")
    print(f"History      : {dt.history()}")
    print(dt.to_pandas())
    print("=" * 60)


def main():
    cfg = load_cfg(str(CFG_FILE))
    delta_base = BASE_DIR / cfg["data"]["deltalake_folder_path"]

    for delta_dir in sorted(delta_base.iterdir()):
        if delta_dir.is_dir():
            try:
                inspect_table(delta_dir)
            except Exception as e:
                print(f"❌ Failed to inspect {delta_dir.name}: {e}")


if __name__ == "__main__":
    main()