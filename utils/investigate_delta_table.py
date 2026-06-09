import json
import sys
from pathlib import Path

from deltalake import DeltaTable
from loguru import logger

sys.path.insert(0, str(Path(__file__).resolve().parent))
from load_config_from_file import load_cfg

PROJECT_ROOT = Path(__file__).resolve().parent.parent
CFG_FILE = PROJECT_ROOT / "configs" / "config.yml"


def inspect_table(delta_path: Path):
    logger.info(f"Inspecting table: {delta_path.name}")
    dt = DeltaTable(str(delta_path))
    print(f"Version  : {dt.version()}")
    print(f"Schema   : {json.loads(dt.schema().to_json())}")
    print(f"Files    : {dt.file_uris()}")
    print(f"History  : {dt.history()}")
    print(dt.to_pandas())


def main():
    cfg = load_cfg(str(CFG_FILE))
    delta_base = PROJECT_ROOT / cfg["data"]["deltalake_folder_path"]

    for delta_dir in sorted(delta_base.iterdir()):
        if delta_dir.is_dir():
            try:
                inspect_table(delta_dir)
            except Exception as e:
                logger.error(f"Failed to inspect '{delta_dir.name}': {e}")


if __name__ == "__main__":
    main()
