---
name: project-pipeline
description: Full batch processing pipeline flow — steps, file roles, config key names, and key design decisions
metadata:
  type: project
---

Pipeline flow implemented on 2026-06-09:

1. `docker compose -f datalake-docker-compose.yaml up -d` — start MinIO + Postgres
2. `python utils/write_delta_table.py` — CSV → Delta Lake at `data_local/delta_lake/`
3. `python utils/upload_data_to_datalake.py` — Delta files → MinIO `raw/delta_lake/`
4. `python utils/investigate_delta_table.py` — inspect local Delta tables
5. `python utils/create_schema.py` — create `staging` + `production` schemas in Postgres
6. `python utils/create_table.py` — create `staging.text_comment_1`, `staging.text_comment_2`, `production.comments`
7. `python batch_processing/main.py` — Spark reads MinIO parquet files, tokenizes with bert-base-uncased, loads to staging

**Why:** User requested full batch processing flow based on logic from `example/` reference code.

**Config keys:** `datalake`, `dw_postgres`, `data`, `spark`, `model` (old keys `data_lake`/`dwh` are gone).

**How to apply:** All scripts run from project root; each inserts its own dir into sys.path for flat imports.
