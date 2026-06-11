import sys
from loguru import logger

from load_config_from_file import load_cfg
from postgresql_client import PostgreSQLClient

CFG_FILE = "./configs/config.yml"

SCHEMAS = ("staging", "production", "stream")


def main():
    cfg = load_cfg(CFG_FILE)["dwh"]

    try:
        with PostgreSQLClient(
            database=cfg["database"],
            user=cfg["user"],
            password=cfg["password"],
            host=cfg.get("host", "localhost"),
            port=cfg.get("port", 5433),
        ) as pc:
            for schema in SCHEMAS:
                try:
                    pc.execute_query(f"CREATE SCHEMA IF NOT EXISTS {schema};")
                    logger.success(f"Schema '{schema}' ready.")
                except Exception as e:
                    logger.error(f"Failed to create schema '{schema}': {e}")
    except Exception as e:
        logger.error(f"Failed to connect to database: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()