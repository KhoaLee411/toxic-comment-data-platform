.PHONY: help up-all down-all up-monitoring up-elk up-airflow up-datalake up-kafka create-network delete-network install clean-all

help:
	@echo "Quản lý Toxic Comment Data Platform"
	@echo ""
	@echo "Các lệnh hỗ trợ:"
	@echo "  make up-all       - Khởi động TẤT CẢ các thành phần"
	@echo "  make down-all     - Tắt TẤT CẢ các thành phần"
	@echo "  make clean-all    - Xóa TẤT CẢ dữ liệu (Volumes & Local Data) để chạy lại từ đầu"
	@echo "  make up-monitoring- Bật Monitoring stack (Prometheus, Grafana)"
	@echo "  make up-elk       - Bật ELK stack (Elasticsearch, Logstash, Kibana, Filebeat)"
	@echo "  make up-airflow   - Bật Airflow orchestration"
	@echo "  make up-datalake  - Bật Data Lake (MinIO, Postgres)"
	@echo "  make up-kafka     - Bật Streaming (Kafka, Zookeeper)"
	@echo "  make install      - Cài đặt thư viện Python từ requirements.txt"

# Khởi động từng phần riêng biệt
up-datalake:
	docker compose -f data_lake_compose.yml up -d

up-kafka:
	docker compose -f stream_kafka_compose.yaml up -d

up-airflow:
	docker compose -f airflow_compose.yaml up -d --build

up-monitoring:
	docker compose --env-file .env.monitoring -f monitoring-compose.yml up -d

up-elk:
	docker compose --env-file .env.monitoring -f elk-compose.yml up -d

# Tắt từng phần
down-datalake:
	docker compose -f data_lake_compose.yml down

down-kafka:
	docker compose -f stream_kafka_compose.yaml down

down-airflow:
	docker compose -f airflow_compose.yaml down

down-monitoring:
	docker compose --env-file .env.monitoring -f monitoring-compose.yml down

down-elk:
	docker compose --env-file .env.monitoring -f elk-compose.yml down

# Khởi động / tắt tất cả
up-all:
	docker network create toxic-platform-network || true
	docker compose -f data_lake_compose.yml -f stream_kafka_compose.yaml -f airflow_compose.yaml -f monitoring-compose.yml -f elk-compose.yml up -d --build

down-all:
	docker compose -f data_lake_compose.yml -f stream_kafka_compose.yaml -f airflow_compose.yaml -f monitoring-compose.yml -f elk-compose.yml down

# Xóa SẠCH SẼ dữ liệu để làm lại từ đầu
clean-all: down-all
	@echo "Đang xóa tất cả Docker Volumes..."
	docker compose -f data_lake_compose.yml -f stream_kafka_compose.yaml -f airflow_compose.yaml -f monitoring-compose.yml -f elk-compose.yml down -v
	@echo "Đang xóa thư mục dữ liệu cục bộ (Local Data)..."
	sudo rm -rf ./data/minio ./data/postgres ./data/kafka ./data/zookeeper
	sudo rm -rf ./data_local/delta_lake ./data_local/stream_checkpoint
	sudo rm -rf ./mlruns ./metrics
	@echo "Đã xóa sạch sẽ toàn bộ dữ liệu! Hệ thống đã quay về trạng thái ban đầu."

# Tạo network
create-network:
	docker network create toxic-platform-network

# Xóa network
delete-network:
	docker network rm toxic-platform-network

# Cài đặt thư viện Python
install:
	pip install -r requirements.txt
	pip install -r airflow/requirements.txt
	pip install -r batch_processing/requirements.txt
	pip install -r model_experiment/requirements.txt
	pip install -r stream_processing/requirements.txt