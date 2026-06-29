# Toxic Comment Data Platform

A robust, production-ready data platform implementing a **Lambda Architecture** for ingesting, validating, transforming, and serving toxic-comment text data. It supports both **batch** (historical data) and **stream** (real-time events) processing pipelines.

## 🚀 Architecture Overview

The platform uses best-in-class data engineering tools to process raw CSVs (`data_local/raw/text_comment_1.csv` & `text_comment_2.csv`) into a final, clean `production.comments` table.

1. **Batch Pipeline (Historical Data)**:
   - **Source**: `text_comment_1.csv`
   - **Ingestion**: Uploaded as Parquet to **MinIO** Data Lake.
   - **Processing**: **PySpark** reads from MinIO, tokenizes text using BERT, and writes to PostgreSQL `staging.batch`.
2. **Stream Pipeline (Live Data)**:
   - **Source**: `text_comment_2.csv`
   - **Simulation**: Python script simulates live insertion into PostgreSQL `stream.raw_comments`.
   - **CDC**: **Debezium** captures row changes and publishes to **Kafka**.
   - **Processing**: **PySpark Structured Streaming** consumes Kafka events, tokenizes, and sinks to `staging.streaming`.
3. **Data Validation (Data Quality)**:
   - **Great Expectations (GX)** strictly validates data inside `staging.batch` and `staging.streaming`.
4. **Data Transformation (dbt)**:
   - **dbt** acts as the unification layer, merging both staging tables, assigning UUIDs where needed, and upserting clean data into the final `production.comments` Data Warehouse table.
5. **Orchestration**:
   - **Apache Airflow** schedules and triggers the pipeline steps.

## 📁 Repository Structure

- `airflow/` - DAGs and Airflow configuration (`ml_pipeline.py`).
- `batch_processing/` - PySpark batch jobs for MinIO ingestion and processing.
- `configs/` - Shared YAML configurations used across all modules.
- `data_transformation/` - **dbt** project containing `schema.yml` and `comments.sql`.
- `data_validation/` - **Great Expectations** project and `validate.py` script.
- `debezium/` - Connector configs and registration scripts.
- `stream_processing/` - PySpark Streaming jobs reading from Kafka.
- `utils/` - Shared scripts like `create_table.py` and `simulate_stream.py`.

## 🛠️ Infrastructure Stacks (Docker Compose)

- **`data_lake_compose.yml`**: MinIO (`:9000`/`:9001`) + PostgreSQL (`:5433`).
- **`stream_kafka_compose.yaml`**: Zookeeper, Kafka, Schema Registry, Debezium, Kafka UI.
- **`airflow_compose.yaml`**: Apache Airflow services.
- **`monitoring-compose.yml`**: Prometheus & Grafana (Optional).

*(All stacks communicate seamlessly via the external `toxic-platform-network`)*

## 🚦 How to Run

### 1. Prerequisites
```bash
# Create shared external network
docker network create toxic-platform-network

# Start core infrastructure (Postgres, MinIO, Kafka)
docker compose -f data_lake_compose.yml up -d
docker compose -f stream_kafka_compose.yaml up -d
```

### 2. Initialization
```bash
# Register Debezium CDC Connector
bash debezium/run.sh register_connector debezium/configs/toxic_comments_cdc.json

# Create DB Schemas and Tables
python utils/create_schema.py
python utils/create_table.py
```

### 3. Execution

**Batch Pipeline:**
```bash
# Process historical data
python batch_processing/main.py
```

**Stream Pipeline:**
```bash
# Terminal 1: Start PySpark Streaming consumer
python stream_processing/main.py

# Terminal 2: Start generating fake stream events
python utils/simulate_stream.py
```

**Validation & Transformation (Orchestrated via Airflow or Manual):**
```bash
# 1. Run Data Quality Checks
python data_validation/validate.py

# 2. Run dbt to merge staging to production
cd data_transformation && dbt run --profiles-dir .
```

## 📝 Coding Guidelines & Gotchas
- **Environment Variables**: Create a `.env` file based on `.env.example` in the root directory. This is ignored by git.
- **`gx/` Config**: The GX context dynamically uses `data_validation/gx` and resolves credentials via python strings.
- **Lambda Strict Isolation**: `text_comment_1.csv` is strictly for batch. `text_comment_2.csv` is strictly for stream simulation to avoid data duplication.
- **Postgres Arrays as JSON**: Data is stored as JSON text arrays (`[101, 2023]`), which is correctly handled by dbt and Great Expectations.
