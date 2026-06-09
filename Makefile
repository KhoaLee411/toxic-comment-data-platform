.PHONY: help up-all down-all up-monitoring up-airflow up-datalake up-kafka up-dvc

help:
	@echo "Quản lý Toxic Comment Data Platform"
	@echo ""
	@echo "Các lệnh hỗ trợ:"
	@echo "  make up-all       - Khởi động TẤT CẢ các thành phần"
	@echo "  make down-all     - Tắt TẤT CẢ các thành phần"
	@echo "  make up-monitoring- Bật Monitoring stack (Prometheus, Grafana, ELK)"
	@echo "  make up-airflow   - Bật Airflow orchestration"
	@echo "  make up-datalake  - Bật Data Lake (MinIO, Postgres)"
	@echo "  make up-kafka     - Bật Streaming (Kafka, Zookeeper)"
	@echo "  make up-dvc       - Bật DVC (remote setup)"

# Khởi động từng phần riêng biệt
up-datalake:
	docker compose -f data_lake_compose.yml up -d

up-kafka:
	docker compose -f stream_kafka_compose.yaml up -d

up-airflow:
	docker compose -f airflow_compose.yaml up -d

up-monitoring:
	docker compose -f monitoring-compose.yml up -d

up-dvc:
	docker compose -f dvc_compose.yml up -d

# Tắt từng phần
down-datalake:
	docker compose -f data_lake_compose.yml down

down-kafka:
	docker compose -f stream_kafka_compose.yaml down

down-airflow:
	docker compose -f airflow_compose.yaml down

down-monitoring:
	docker compose -f monitoring-compose.yml down

down-dvc:
	docker compose -f dvc_compose.yml down

# Khởi động / tắt tất cả
up-all:
	docker network create shared-network || true
	docker compose -f data_lake_compose.yml -f stream_kafka_compose.yaml -f airflow_compose.yaml -f monitoring-compose.yml -f dvc_compose.yml up -d

down-all:
	docker compose -f data_lake_compose.yml -f stream_kafka_compose.yaml -f airflow_compose.yaml -f monitoring-compose.yml -f dvc_compose.yml down
