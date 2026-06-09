import sys
import time
from pathlib import Path

import pandas as pd
from loguru import logger

sys.path.insert(0, str(Path(__file__).resolve().parent))
from load_config_from_file import load_cfg
from postgresql_client import PostgresSQLClient

PROJECT_ROOT = Path(__file__).resolve().parent.parent
CFG_FILE = PROJECT_ROOT / "configs" / "config.yml"


def main():
    cfg = load_cfg(str(CFG_FILE))
    pg_cfg = cfg["dw_postgres"]
    stream_cfg = cfg["stream"]

    table_name = stream_cfg["table"]
    sleep_secs = stream_cfg.get("sleep_secs", 2)
    csv_dir = PROJECT_ROOT / cfg["data"]["local_path"]

    pc = PostgresSQLClient(
        database=pg_cfg["database"],
        user=pg_cfg["user"],
        password=pg_cfg["password"],
        host=pg_cfg.get("host", "localhost"),
        port=pg_cfg.get("port", 5433),
    )

    columns = pc.get_columns(table_name=table_name)
    insert_columns = [c for c in columns if c not in ("id", "created_at")]
    if not insert_columns:
        raise RuntimeError(f"No writable columns found in {table_name}")

    logger.info(f"Streaming into {table_name} — columns: {insert_columns}")

    placeholders = ",".join(["%s"] * len(insert_columns))
    col_list = ",".join(insert_columns)
    insert_sql = f"INSERT INTO {table_name} ({col_list}) VALUES ({placeholders})"

    for csv_file in sorted(csv_dir.glob("*.csv")):
        logger.info(f"Processing {csv_file.name}")
        df = pd.read_csv(csv_file)

        for idx, row in df.iterrows():
            values = tuple(row[c] for c in insert_columns)
            try:
                pc.execute_query_params(insert_sql, values)
                logger.info(f"Inserted row {idx}: {dict(zip(insert_columns, values))}")
            except Exception as e:
                logger.error(f"Row {idx} failed: {e}")
            time.sleep(sleep_secs)

    pc.close()
    logger.success("Streaming simulation complete.")


if __name__ == "__main__":
    main()
