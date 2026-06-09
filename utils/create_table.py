import sys
from pathlib import Path

from loguru import logger

sys.path.insert(0, str(Path(__file__).resolve().parent))
from load_config_from_file import load_cfg
from postgresql_client import PostgresSQLClient

PROJECT_ROOT = Path(__file__).resolve().parent.parent
CFG_FILE = PROJECT_ROOT / "configs" / "config.yml"

TABLE_DEFINITIONS = [
    # Batch processing targets (staging schema)
    """
    CREATE TABLE IF NOT EXISTS staging.text_comment_1 (
        labels         BIGINT,
        input_ids      TEXT,
        attention_mask TEXT
    );
    """,
    """
    CREATE TABLE IF NOT EXISTS staging.text_comment_2 (
        labels         BIGINT,
        input_ids      TEXT,
        attention_mask TEXT
    );
    """,
    # Stream processing source — Debezium CDC watches this table
    """
    CREATE TABLE IF NOT EXISTS stream.raw_comments (
        id           SERIAL PRIMARY KEY,
        comment_text TEXT,
        labels       BIGINT,
        created_at   TIMESTAMP DEFAULT NOW()
    );
    """,
    # Shared production destination — batch and stream both write here
    """
    CREATE TABLE IF NOT EXISTS production.comments (
        id             SERIAL PRIMARY KEY,
        labels         BIGINT,
        input_ids      TEXT,
        attention_mask TEXT,
        inserted_at    TIMESTAMP DEFAULT NOW()
    );
    """,
]


def main():
    cfg = load_cfg(str(CFG_FILE))["dw_postgres"]
    pc = PostgresSQLClient(
        database=cfg["database"],
        user=cfg["user"],
        password=cfg["password"],
        host=cfg.get("host", "localhost"),
        port=cfg.get("port", 5433),
    )

    for ddl in TABLE_DEFINITIONS:
        table_name = ddl.strip().split("EXISTS")[1].strip().split()[0]
        try:
            pc.execute_query(ddl)
            logger.success(f"Table '{table_name}' ready.")
        except Exception as e:
            logger.error(f"Failed to create table '{table_name}': {e}")

    pc.close()


if __name__ == "__main__":
    main()
