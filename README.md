# CLAUDE.md

Guidance for Claude Code working in this repository.

## What this is

A data platform for ingesting toxic-comment text data into a local data lake + data
warehouse stack, supporting both **batch** and **stream** processing paths.

Raw CSVs (`comment_text,labels`) in `data_local/raw/` are processed via two pipelines:

- **Batch**: CSV → Delta Lake → MinIO → PySpark tokenization → PostgreSQL staging
- **Stream**: PostgreSQL CDC (Debezium) → Kafka → PySpark Structured Streaming → PostgreSQL production

## Architecture

### Infrastructure

- **`data_lake_compose.yml`** — MinIO + PostgreSQL stack:
  - `minio` — API `:9000`, console `:9001`, data at `./data/minio`
  - `postgres:16` — host port `5433` → container `5432`, `wal_level=logical` (CDC-ready)
- **`stream_kafka_compose.yaml`** — Kafka + Debezium stack:
  - Zookeeper, Kafka broker, Schema Registry, Debezium Connect, Debezium UI
  - Debezium UI at `:8085`, Kafka Control Center at `:9021`
  - Both compose files join the **external** Docker network `toxic-platform-network`

### Config & Utilities

- **`configs/config.yml`** — single source of config (`datalake`, `dw_postgres`, `data`, `spark`, `model`, `stream` sections). Uses `${VAR}` env placeholders.
- **`utils/load_config_from_file.py`** — `load_cfg()` loads YAML, calls `load_dotenv()`, expands `${VAR}` via `os.path.expandvars`.
- **`utils/postgresql_client.py`** — `psycopg2` wrapper: `execute_query()`, `execute_query_params()`, `get_columns()`.

### Processing Modules

- **`batch_processing/spark_session.py`** — `create_spark_session()`, shared by both pipelines.
- **`batch_processing/minio_config.py`** — `load_minio_config()`, configures Hadoop S3A connector.
- **`batch_processing/main.py`** — reads parquet from MinIO, tokenizes with BERT (pandas batch), writes to `staging`.
- **`stream_processing/main.py`** — reads Kafka CDC events (Debezium JSON), tokenizes with BERT UDF, writes to `production`.

## Pipeline Flow

### Batch Processing

```
docker compose -f data_lake_compose.yml up -d
         ↓
python utils/csv_to_delta_table.py      # CSV → Delta Lake (data_local/delta_lake/)
python utils/upload_data_to_datalake.py  # Delta files → MinIO raw/delta_lake/
python utils/investigate_delta_table.py  # Inspect local Delta tables (optional)
         ↓
python utils/create_schema.py            # CREATE SCHEMA staging, production, stream
python utils/create_table.py             # CREATE TABLE staging.*, stream.raw_comments, production.comments
         ↓
python batch_processing/main.py          # Spark: MinIO → BERT tokenize → staging.*
```

### Stream Processing

```
docker compose -f stream_kafka_compose.yaml up -d
         ↓
bash debezium/run.sh register_connector debezium/configs/toxic_comments_cdc.json
         ↓
python utils/simulate_stream.py   # Simulate: insert CSV rows into stream.raw_comments (2s delay)
         ↓ (Debezium CDC: stream.raw_comments → Kafka topic)
python stream_processing/main.py            # Spark readStream: Kafka → hf_tokenize UDF → production.comments
```

## Running

```bash
# One-time setup
docker network create toxic-platform-network

# Batch pipeline
docker compose -f data_lake_compose.yml up -d
python utils/write_delta_table.py
python utils/upload_data_to_datalake.py
python utils/create_schema.py
python utils/create_table.py
python batch_processing/main.py

# Stream pipeline (requires batch setup to have run first for schemas/tables)
docker compose -f stream_kafka_compose.yaml up -d
bash debezium/run.sh register_connector debezium/configs/toxic_comments_cdc.json
python utils/simulate_stream.py   # terminal 1
python stream_processing/main.py  # terminal 2
```

### Required `.env` (gitignored)

```
MINIO_ROOT_USER=...
MINIO_ROOT_PASSWORD=...
POSTGRES_DB=...
POSTGRES_USER=...
POSTGRES_PASSWORD=...
```

## Coding Conventions

- **snake_case** for all file and folder names (except README.md, Dockerfile, .gitignore, .env).
- **loguru** (`from loguru import logger`) for all logging — no stdlib `logging` or `print` in processing code.
- **`PROJECT_ROOT`** as the canonical root path variable in every script.
- Config loaded at module level via `cfg = load_cfg(str(CFG_FILE))`; tokenizer loaded at module level (expensive init).
- All scripts runnable from project root — each inserts its own directory into `sys.path`.
- Error handling: `try/except Exception as e: logger.error(...)` — never silent failures.

## Gotchas

- **`data/` and `.env` are gitignored.** Never commit them.
- **`data_local/delta_lake/` is gitignored.** Created at runtime by `write_delta_table.py`.
- **`stream_processing/main.py` imports `create_spark_session` from `batch_processing/`** — intentional reuse.
- **BERT tokenizer downloads on first run** (`bert-base-uncased`). Ensure internet access or a local HuggingFace cache.
- **Debezium topic name** is `toxic_comments.stream.raw_comments` (prefix.schema.table from connector config).
- **`stream_checkpoint/`** is written to `data_local/stream_checkpoint/` — gitignored via `data_local/`.
- Install all deps: `pip install -r requirements.txt`
