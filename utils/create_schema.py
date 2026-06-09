import sys
from pathlib import Path

from loguru import logger

sys.path.insert(0, str(Path(__file__).resolve().parent))
from load_config_from_file import load_cfg
from postgresql_client import PostgreSQLClient

PROJECT_ROOT = Path(__file__).resolve().parent.parent
CFG_FILE = PROJECT_ROOT / "configs" / "config.yml"


def main():
    cfg = load_cfg(str(CFG_FILE))["dw_postgres"]

    with PostgreSQLClient(
        database=cfg["database"],
        user=cfg["user"],
        password=cfg["password"],
        host=cfg.get("host", "localhost"),
        port=cfg.get("port", 5433),
    ) as pc:
        for schema in ("staging", "production", "stream"):
            try:
                pc.execute_query(f"CREATE SCHEMA IF NOT EXISTS {schema};")
                logger.success(f"Schema '{schema}' ready.")
            except Exception as e:
                logger.error(f"Failed to create schema '{schema}': {e}")


if __name__ == "__main__":
    main()
