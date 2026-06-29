# Toxic Comment Data Platform

A robust, production-ready data platform implementing a **Lambda Architecture** for ingesting, validating, transforming, and serving toxic-comment text data. It supports both **batch** (historical data) and **stream** (real-time events) processing pipelines, alongside full **MLOps** model lifecycle management and **Monitoring**.

## 🚀 Architecture Overview

The platform uses best-in-class data engineering tools to process raw CSVs (`data_local/raw/text_comment_1.csv` & `text_comment_2.csv`) into a final, clean `production.comments` table, trains ML models on it, and monitors the entire infrastructure.

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
5. **Model Experimentation (MLOps)**:
   - **DVC** orchestrates the ML pipeline (Extract → Train → Evaluate → Register).
   - **MLflow** tracks metrics, parameters, and model registry artifacts.
6. **Orchestration**:
   - **Apache Airflow** schedules and triggers the end-to-end pipeline (`data_prep → data_quality → data_transform → model_exp`).
7. **Monitoring & Logging**:
   - **Prometheus & Grafana**: System and container metrics.
   - **ELK Stack (Elasticsearch, Logstash, Kibana) + Filebeat**: Centralized system log aggregation.

## 📁 Repository Structure

- `airflow/` - DAGs and Airflow configuration (`ml_pipeline.py`).
- `batch_processing/` - PySpark batch jobs for MinIO ingestion and processing.
- `configs/` - Shared YAML configurations used across all modules.
- `data_transformation/` - **dbt** project containing `schema.yml` and `comments.sql`.
- `data_validation/` - **Great Expectations** project and `validate.py` script.
- `debezium/` - Connector configs and registration scripts.
- `model_experiment/` - ML training scripts split into DVC stages.
- `monitoring/` - Configuration for Prometheus, Grafana, Alertmanager, ELK, and Filebeat.
- `stream_processing/` - PySpark Streaming jobs reading from Kafka.
- `utils/` - Shared scripts like `create_table.py` and `simulate_stream.py`.

## 🛠️ Infrastructure Stacks (Docker Compose)

- **`data_lake_compose.yml`**: MinIO (`:9000`/`:9001`) + PostgreSQL (`:5433`).
- **`stream_kafka_compose.yaml`**: Zookeeper, Kafka, Schema Registry, Debezium, Kafka UI.
- **`airflow_compose.yaml`**: Apache Airflow orchestration.
- **`monitoring-compose.yml`**: Prometheus, Grafana, Alertmanager, Node Exporter, cAdvisor.
- **`elk-compose.yml`**: Elasticsearch, Logstash, Kibana, Filebeat.

*(All stacks communicate seamlessly via the external `toxic-platform-network`)*

## 🚦 How to Run

### 1. Prerequisites
```bash
# Create shared external network
docker network create toxic-platform-network

# Copy environment variables
cp .env.example .env
cp .env.monitoring.example .env.monitoring

# Start core infrastructure
docker compose -f data_lake_compose.yml up -d
docker compose -f stream_kafka_compose.yaml up -d

# Start Airflow & Monitoring
docker compose -f airflow_compose.yaml up -d --build
docker compose --env-file .env.monitoring -f monitoring-compose.yml up -d
docker compose --env-file .env.monitoring -f elk-compose.yml up -d
```

### 2. Initialization
```bash
# Register Debezium CDC Connector
bash debezium/run.sh register_connector debezium/configs/toxic_comments_cdc.json

# Create DB Schemas and Tables
python utils/create_schema.py
python utils/create_table.py
```

### 3. Execution via Airflow
The entire pipeline is fully automated. Open the Airflow Web UI (`http://localhost:8082`) and trigger the `end_to_end_ml_pipeline` DAG.

### 4. Manual Execution (Optional)
If you prefer running components manually:
```bash
# Batch Data Prep
python batch_processing/main.py

# Data Validation
python data_validation/validate.py --source postgres
python data_validation/validate.py --source stream

# Data Transformation
cd data_transformation && dbt run --profiles-dir . && cd ..

# ML Experimentation (DVC)
dvc repro
```

## 📝 Coding Guidelines & Gotchas
- **Environment Variables**: `.env` and `.env.monitoring` handle sensitive secrets and are ignored by git. Keep them populated locally.
- **DVC Tracking**: Only `metrics/` is committed to git. Checkpoints are cached remotely.
- **Lambda Strict Isolation**: `text_comment_1.csv` is strictly for batch. `text_comment_2.csv` is strictly for stream simulation to avoid data duplication.
- **Monitoring Alerts**: Alertmanager routes to Discord based on `DISCORD_WEBHOOK_URL` in `.env.monitoring`.
