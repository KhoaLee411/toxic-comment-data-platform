# Nền Tảng Dữ Liệu Phân Loại Bình Luận Độc Hại (Toxic Comment Data Platform)

Một nền tảng dữ liệu mạnh mẽ, sẵn sàng cho môi trường sản xuất (production-ready) áp dụng **Kiến trúc Lambda (Lambda Architecture)** để thu thập, kiểm định, chuyển đổi và cung cấp dữ liệu văn bản bình luận độc hại. Hệ thống hỗ trợ xử lý song song cả hai luồng **Batch** (dữ liệu lịch sử) và **Stream** (sự kiện thời gian thực), tích hợp toàn diện quy trình quản lý vòng đời mô hình **MLOps** và Hệ thống **Giám sát (Monitoring)**.

## 🚀 Tổng Quan Kiến Trúc

Nền tảng sử dụng các công cụ Data Engineering hàng đầu để xử lý các file CSV thô (`data_local/raw/text_comment_1.csv` & `text_comment_2.csv`) thành một bảng dữ liệu sạch duy nhất `production.comments`. Sau đó, hệ thống sẽ tự động huấn luyện mô hình Machine Learning trên dữ liệu này và giám sát toàn bộ tài nguyên hạ tầng.

1. **Luồng Xử Lý Batch (Dữ liệu Lịch Sử)**:
   - **Nguồn**: `text_comment_1.csv`
   - **Thu thập (Ingestion)**: Upload định dạng Parquet lên Data Lake **MinIO**.
   - **Xử lý (Processing)**: **PySpark** đọc dữ liệu từ MinIO, tách từ (tokenize) bằng mô hình BERT, và ghi vào PostgreSQL tại bảng `staging.batch`.
2. **Luồng Xử Lý Stream (Dữ liệu Thời Gian Thực)**:
   - **Nguồn**: `text_comment_2.csv`
   - **Giả lập (Simulation)**: Script Python giả lập việc chèn liên tục dữ liệu trực tiếp vào PostgreSQL tại bảng `stream.raw_comments`.
   - **CDC (Change Data Capture)**: **Debezium** bắt các thay đổi của dòng dữ liệu và đẩy bản tin lên **Kafka**.
   - **Xử lý (Processing)**: **PySpark Structured Streaming** tiêu thụ (consume) sự kiện từ Kafka, tokenize, và ghi vào bảng `staging.streaming`.
3. **Kiểm Định Dữ Liệu (Data Quality)**:
   - **Great Expectations (GX)** kiểm tra nghiêm ngặt chất lượng và định dạng dữ liệu nằm trong `staging.batch` và `staging.streaming`.
4. **Chuyển Đổi Dữ Liệu (dbt)**:
   - **dbt** đóng vai trò là tầng hợp nhất, gộp cả hai bảng staging lại, cấp phát UUID tự động cho dữ liệu batch (nếu cần), và ghi đè/cập nhật dữ liệu sạch vào bảng Data Warehouse cuối cùng là `production.comments`.
5. **Thử Nghiệm Mô Hình (MLOps)**:
   - **DVC** điều phối luồng huấn luyện Machine Learning theo các chặng (Extract → Train → Evaluate → Register).
   - **MLflow** theo dõi các chỉ số (metrics), siêu tham số (parameters) và lưu trữ mô hình (model registry).
6. **Điều Phối Tự Động (Orchestration)**:
   - **Apache Airflow** lập lịch và kích hoạt toàn bộ đường ống dẫn dữ liệu từ đầu đến cuối (`data_prep → data_quality → data_transform → model_exp`).
7. **Giám Sát & Ghi Log (Monitoring)**:
   - **Prometheus & Grafana**: Thu thập và trực quan hóa chỉ số hoạt động của Server và các Docker Container.
   - **ELK Stack (Elasticsearch, Logstash, Kibana) + Filebeat**: Thu thập và quản lý log tập trung cho toàn bộ hệ thống.

## 📁 Cấu Trúc Thư Mục

- `airflow/` - Chứa file cấu hình DAGs của Airflow (`ml_pipeline.py`).
- `batch_processing/` - Các job PySpark để đẩy dữ liệu lên MinIO và xử lý theo lô.
- `configs/` - Các cấu hình YAML dùng chung cho nhiều module.
- `data_transformation/` - Dự án **dbt** chứa `schema.yml` và câu lệnh SQL `comments.sql`.
- `data_validation/` - Dự án **Great Expectations** và script chạy `validate.py`.
- `debezium/` - Cấu hình connector bắt sự kiện CDC và script đăng ký.
- `model_experiment/` - Script huấn luyện ML được chia nhỏ thành các stage của DVC.
- `monitoring/` - Cấu hình cho cụm Prometheus, Grafana, Alertmanager, ELK, và Filebeat.
- `stream_processing/` - Job PySpark Streaming đọc dữ liệu từ Kafka.
- `utils/` - Các script dùng chung (VD: `create_table.py` và `simulate_stream.py`).

## 🛠️ Hạ Tầng Hệ Thống (Docker Compose)

- **`data_lake_compose.yml`**: Chứa MinIO (`:9000`/`:9001`) + PostgreSQL (`:5433`).
- **`stream_kafka_compose.yaml`**: Zookeeper, Kafka, Schema Registry, Debezium, Kafka UI.
- **`airflow_compose.yaml`**: Hệ thống điều phối Apache Airflow.
- **`monitoring-compose.yml`**: Prometheus, Grafana, Alertmanager, Node Exporter, cAdvisor.
- **`elk-compose.yml`**: Elasticsearch, Logstash, Kibana, Filebeat.

*(Tất cả các thành phần này giao tiếp mượt mà với nhau thông qua mạng ảo external: `toxic-platform-network`)*

## 🚦 Hướng Dẫn Chạy Hệ Thống

### 1. Chuẩn bị (Prerequisites)
```bash
# Tạo mạng dùng chung cho các container
docker network create toxic-platform-network

# Copy các file biến môi trường
cp .env.example .env
cp .env.monitoring.example .env.monitoring

# Khởi động hạ tầng lõi (Core Infrastructure)
docker compose -f data_lake_compose.yml up -d
docker compose -f stream_kafka_compose.yaml up -d

# Khởi động Airflow & Hệ thống Giám sát
docker compose -f airflow_compose.yaml up -d --build
docker compose --env-file .env.monitoring -f monitoring-compose.yml up -d
docker compose --env-file .env.monitoring -f elk-compose.yml up -d
```

### 2. Khởi tạo (Initialization)
```bash
# Đăng ký Connector CDC với Debezium
bash debezium/run.sh register_connector debezium/configs/toxic_comments_cdc.json

# Khởi tạo Schema và các Bảng trong Database
python utils/create_schema.py
python utils/create_table.py
```

### 3. Vận Hành Tự Động Qua Airflow
Toàn bộ luồng xử lý đã được tự động hóa. Hãy mở giao diện **Airflow Web UI** (`http://localhost:8082`) và kích hoạt (Trigger) DAG có tên là `end_to_end_ml_pipeline`.

### 4. Vận Hành Thủ Công (Tùy chọn)
Nếu bạn muốn chạy từng bước bằng tay để kiểm tra:
```bash
# Xử lý Batch
python batch_processing/main.py

# Kiểm định Dữ Liệu (Data Validation)
python data_validation/validate.py --source postgres
python data_validation/validate.py --source stream

# Chuyển đổi Dữ Liệu (dbt)
cd data_transformation && dbt run --profiles-dir . && cd ..

# Huấn luyện Mô hình (DVC)
dvc repro
```

## 📝 Quy Ước Lập Trình & Lưu Ý
- **Biến Môi Trường (Env Variables)**: `.env` và `.env.monitoring` chứa các thông tin nhạy cảm và sẽ bị bỏ qua bởi git (gitignore). Hãy chắc chắn bạn đã điền đủ thông tin ở máy tính cá nhân.
- **Theo Dõi DVC**: Chỉ có thư mục `metrics/` được commit lên Git. Các file Checkpoint của model được cache lại ở xa (Remote Storage).
- **Phân Lập Kiến Trúc Lambda Tách Bạch**: `text_comment_1.csv` chỉ được dùng riêng cho Batch. `text_comment_2.csv` chỉ được dùng để giả lập luồng Stream. Điều này giúp ngăn chặn hoàn toàn việc nhân đôi dữ liệu.
- **Thông Báo Giám Sát (Alerts)**: Alertmanager sẽ tự động nhắn tin cảnh báo lỗi về kênh Discord dựa vào biến `DISCORD_WEBHOOK_URL` trong file `.env.monitoring`.
