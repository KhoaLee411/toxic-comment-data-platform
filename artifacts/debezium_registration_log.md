# Đăng ký và Kích hoạt Debezium CDC

Debezium (Change Data Capture) đóng vai trò cực kỳ quan trọng trong luồng Streaming của hệ thống. Nó chịu trách nhiệm "bắt" (capture) mọi thay đổi chèn dữ liệu vào bảng `stream.raw_comments` trên PostgreSQL và tự động bắn các thay đổi đó lên Kafka theo thời gian thực (Real-time).

Dưới đây là minh chứng quá trình đăng ký Connector thành công với hệ thống Debezium.

## 1. Đăng Ký Connector CDC

**Lệnh thực thi:**
```bash
bash debezium/run.sh register_connector debezium/configs/toxic_comments_cdc.json
```

**Output thu được (Log kết nối thành công):**
```text
Registering connector from debezium/configs/toxic_comments_cdc.json
HTTP/1.1 201 Created
Date: Wed, 01 Jul 2026 17:25:20 GMT
Location: http://localhost:8083/connectors/toxic-comments-cdc
Content-Type: application/json
Content-Length: 504
Server: Jetty(9.4.44.v20210927)

{
  "name": "toxic-comments-cdc",
  "config": {
    "connector.class": "io.debezium.connector.postgresql.PostgresConnector",
    "database.hostname": "postgres",
    "database.port": "5432",
    "database.user": "postgres",
    "database.dbname": "toxic_comment_db",
    "plugin.name": "pgoutput",
    "publication.name": "dbz_publication",
    "publication.autocreate.mode": "disabled",
    "table.include.list": "stream.raw_comments",
    "database.server.name": "toxic_comments",
    "name": "toxic-comments-cdc"
  },
  "tasks": [],
  "type": "source"
}
```
*(Debezium đã kết nối thành công với PostgreSQL qua plugin `pgoutput` và bắt đầu theo dõi bảng `stream.raw_comments`)*

## 2. Kiểm Tra Trạng Thái Hoạt Động (Status)

Để chắc chắn Connector không bị crash sau khi khởi tạo, chúng ta gọi API kiểm tra trạng thái:

**Lệnh thực thi:**
```bash
curl -s http://localhost:8083/connectors/toxic-comments-cdc/status | jq
```

**Output thu được:**
```json
{
  "name": "toxic-comments-cdc",
  "connector": {
    "state": "RUNNING",
    "worker_id": "172.24.0.7:8083"
  },
  "tasks": [
    {
      "id": 0,
      "state": "RUNNING",
      "worker_id": "172.24.0.7:8083"
    }
  ],
  "type": "source"
}
```

👉 **Kết luận:** Trạng thái tổng quát của Connector và các Task nội bộ đều đang ở mức **"RUNNING"** khỏe mạnh. Luồng Stream Real-time từ Database sang Kafka đã chính thức thông suốt.
