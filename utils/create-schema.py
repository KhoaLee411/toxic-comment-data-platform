import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from load_config_from_file import load_cfg
from postgresql_client import PostgresSQLClient

BASE_DIR = Path(__file__).resolve().parent.parent
CFG_FILE = BASE_DIR / "configs" / "config.yml"


def main():
    cfg = load_cfg(str(CFG_FILE))["dw_postgres"]
    pc = PostgresSQLClient(
        database=cfg["database"],
        user=cfg["user"],
        password=cfg["password"],
        host=cfg.get("host", "localhost"),
        port=cfg.get("port", 5433),
    )

    schemas = ["staging", "production"]
    for schema in schemas:
        try:
            pc.execute_query(f"CREATE SCHEMA IF NOT EXISTS {schema};")
        except Exception as e:
            print(f"❌ Failed to create schema '{schema}': {e}")

    pc.close()


if __name__ == "__main__":
    main()