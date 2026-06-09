import sys
from pathlib import Path

from loguru import logger

sys.path.insert(0, str(Path(__file__).resolve().parent))
from load_config_from_file import load_cfg
from postgresql_client import PostgreSQLClient

PROJECT_ROOT = Path(__file__).resolve().parent.parent
CFG_FILE = PROJECT_ROOT / "configs" / "config.yml"

# (table_name, ddl) — explicit name avoids fragile DDL string parsing
TABLE_DEFINITIONS: list[tuple[str, str]] = [
    ("staging.text_comment_1", """
        CREATE TABLE IF NOT EXISTS staging.text_comment_1 (
            labels         BIGINT,
            input_ids      TEXT,
            attention_mask TEXT
        );
    """),
    ("staging.text_comment_2", """
        CREATE TABLE IF NOT EXISTS staging.text_comment_2 (
            labels         BIGINT,
            input_ids      TEXT,
            attention_mask TEXT
        );
    """),
    ("stream.raw_comments", """
        CREATE TABLE IF NOT EXISTS stream.raw_comments (
            id           SERIAL PRIMARY KEY,
            comment_text TEXT,
            labels       BIGINT,
            created_at   TIMESTAMP DEFAULT NOW()
        );
    """),
    ("production.comments", """
        CREATE TABLE IF NOT EXISTS production.comments (
            id             SERIAL PRIMARY KEY,
            labels         BIGINT,
            input_ids      TEXT,
            attention_mask TEXT,
            inserted_at    TIMESTAMP DEFAULT NOW()
        );
    """),
]


def main():
    cfg = load_cfg(str(CFG_FILE))["dw_postgres"]

    with PostgreSQLClient(
        database=cfg["database"],
        user=cfg["user"],
        password=cfg["password"],
        host=cfg.get("host", "localhost"),
        port=cfg.get("port", 5433),
    ) as pc:
        for table_name, ddl in TABLE_DEFINITIONS:
            try:
                pc.execute_query(ddl)
                logger.success(f"Table '{table_name}' ready.")
            except Exception as e:
                logger.error(f"Failed to create table '{table_name}': {e}")


if __name__ == "__main__":
    main()
