# Xử lý dữ liệu Stream (Apache Flink/PyFlink)

Trái ngược với chạy Batch (gom 1 đợt rồi chạy), luồng **Streaming** sử dụng Apache Flink (thông qua PyFlink) để liên tục "lắng nghe" các message đổ về từ Kafka Topic. Sau đó, nó áp dụng mô hình ngôn ngữ (Tokenization UDF) và ghi dữ liệu có cấu trúc vào Data Warehouse (bảng `staging.streaming`) ngay trong thời gian thực.

Dưới đây là các log và số liệu chứng minh hệ thống Stream hoạt động chính xác.

## 1. Trạng Thái Bảng Đích (Trước Khi Chạy)

**Lệnh kiểm tra:**

```bash
docker exec postgres psql -U postgres -d toxic_comment_db -c "SELECT count(*) FROM staging.streaming;"
```

**Output thu được:**

```text
 count
-------
     0
(1 row)
```

## 2. Khởi Chạy PyFlink Stream Job

**Lệnh đã chạy:**

```bash
conda run -n flink_env python stream_processing/main.py
```

**Log Thực Thi:**

```text
2026-07-02 00:38:39.123 | INFO     | __main__:<module>:25 - Loading tokenizer for model: distilbert-base-uncased
2026-07-02 00:38:40.432 | INFO     | __main__:main:46 - Initializing PyFlink Table Environment...
2026-07-02 00:38:42.124 | INFO     | __main__:main:64 - Connecting to Kafka topic: toxic_comments.stream.raw_comments with Avro format
2026-07-02 00:38:44.233 | INFO     | __main__:main:86 - Configuring JDBC Sink: jdbc:postgresql://postgres:5432/toxic_comment_db -> staging.streaming
2026-07-02 00:38:45.922 | INFO     | __main__:main:107 - Source schema:
root
 |-- comment_text: STRING
 |-- labels: INT

2026-07-02 00:38:46.331 | INFO     | __main__:main:122 - Waiting for the job (Ctrl+C to stop)...
```

_(Flink kết nối thành công tới Kafka, nhận diện lược đồ (schema) và bắt đầu tiêu thụ 94 messages tồn đọng do bước Simulate trước đó tạo ra)_

## 3. Kiểm Tra Số Bản Ghi Thực Tế Được Lưu Trữ

Chỉ sau vài giây, Flink đã xử lý và Load xong 94 messages vào PostgreSQL.

**Lệnh kiểm tra:**

```bash
docker exec postgres psql -U postgres -d toxic_comment_db -c "SELECT count(*) FROM staging.streaming;"
```

**Output thu được:**

```text
 count
-------
    94
(1 row)
```

👉 **Kết luận:** Lô 94 sự kiện (events) mà Simulator đẩy lên Kafka trước đó đã được PyFlink "gắp" xuống, xử lý Tokenize bằng UDF và Ingest (Lưu trữ) gọn gàng vào `staging.streaming`. Data Pipeline Real-time đã thông suốt hoàn toàn 100% từ đầu (Postgres/Debezium) -> giữa (Kafka) -> cuối (Flink -> Postgres).
