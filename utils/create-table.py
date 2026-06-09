import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from load_config_from_file import load_cfg
from postgresql_client import PostgresSQLClient

BASE_DIR = Path(__file__).resolve().parent.parent
CFG_FILE = BASE_DIR / "configs" / "config.yml"

TABLE_DEFINITIONS = [
    """
    CREATE TABLE IF NOT EXISTS staging.text_comment_1 (
        labels      BIGINT,
        input_ids   TEXT,
        attention_mask TEXT
    );
    """,
    """
    CREATE TABLE IF NOT EXISTS staging.text_comment_2 (
        labels      BIGINT,
        input_ids   TEXT,
        attention_mask TEXT
    );
    """,
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
        try:
            pc.execute_query(ddl)
        except Exception as e:
            print(f"❌ Failed to create table: {e}")

    pc.close()


if __name__ == "__main__":
    main()