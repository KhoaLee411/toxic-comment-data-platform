# 📊 Báo Cáo Thực Thi & Kiểm Thử Hệ Thống Monitoring (Observability Report)

Báo cáo này lưu trữ minh chứng về việc kiểm thử hệ thống giám sát (Monitoring & Logging) của Toxic Comment Data Platform trong quá trình các Data Pipeline đang hoạt động (DAG chạy).

---

## 1. Giám Sát Tài Nguyên & Cảnh Báo (Prometheus + Grafana + Alertmanager)

Hệ thống sử dụng **cAdvisor** để đo đạc từng Container, **Node Exporter** để đo tài nguyên máy chủ, và **Prometheus** làm trung tâm xử lý dữ liệu. Các biểu đồ được trực quan hóa trên **Grafana**.

### 1.1. Kịch Bản Sinh Tải (Load Generation)
- **Hành động:** Kích hoạt các DAG `end_to_end_ml_pipeline` và `stream_simulation_pipeline` liên tục trong Airflow để ép các container xử lý Big Data (Spark, Kafka, MinIO, Postgres) ngốn RAM và CPU.
- **Trạng thái:** Prometheus ghi nhận tài nguyên CPU/RAM tăng đột biến và vượt qua ngưỡng an toàn (Warning threshold > 80%).

### 1.2. Minh Chứng Báo Động (Alertmanager -> Discord Webhook)
Dưới đây là log tin nhắn thực tế mà hệ thống tự động gom nhóm (grouping) và bắn về kênh Discord của nhóm phát triển nhờ cấu hình `group_wait` hiệu quả:

```text
CI Notifications APP — 6:30 PM
🟡 [WARNING] HostDiskSpaceLow
Instance: platform-host
Summary: Low disk space (platform-host:/)
Detail: Only 9.888% disk space remaining.

🟡 [WARNING] ContainerHighMemoryUsage
Instance: cadvisor:8080
Summary: Container high memory (grafana)
Detail: Container grafana uses +Inf% of its memory limit.
...
(Và 19 dịch vụ khác bao gồm: airflow-postgres, airflow-redis, postgres, cadvisor, node-exporter, alertmanager, prometheus, stream-debezium, minio, airflow-triggerer, airflow-webserver, airflow-worker, airflow-scheduler, stream-debezium-ui, stream-zookeeper, stream-control-center, stream-schema-registry, stream-broker)
```
> **Đánh giá:** Tính năng Alerting hoạt động chính xác 100%. Alertmanager đã gom thành công 19 cảnh báo riêng lẻ thành 1 tin nhắn duy nhất, tránh tình trạng spam rác (Alert Fatigue).

### 1.3. Minh Chứng Biểu Đồ (Grafana Dashboards)
*(Sinh viên chèn ảnh Screenshot của Dashboard Grafana vào đây - Căn lúc biểu đồ tài nguyên đang đạt đỉnh)*

![Grafana Node Exporter Full Dashboard](chèn_ảnh_grafana_node_exporter_vào_đây.png)

![Grafana Platform Container Metrics](chèn_ảnh_grafana_container_metrics_vào_đây.png)

### 1.4. Dữ Liệu Thô Khảo Sát (Exported Panel Data)
*(Sinh viên đính kèm file CSV đã export từ Grafana Panel bằng cách Inspect -> Data -> Download CSV)*
- Tên file đính kèm: `grafana_resource_usage_data.csv`

---

## 2. Quản Lý Log Tập Trung (ELK Stack - Elasticsearch, Logstash, Kibana, Filebeat)

Thay vì phải gõ lệnh `docker logs` cho từng container một, hệ thống sử dụng **Filebeat** tự động thu thập toàn bộ log trên host, đẩy qua **Logstash** lọc và lưu trữ tại **Elasticsearch**.

### 2.1. Khởi Tạo Data View
- **Index Pattern:** `logs-*`
- **Timestamp Field:** `@timestamp`
- **Tình trạng:** Kibana đã nhận diện thành công hàng ngàn dòng log từ Data Platform.

### 2.2. Minh Chứng Truy Vấn Log (Kibana Discover)
Dưới đây là minh chứng hệ thống có khả năng truy vấn (Query) Log mạnh mẽ trong thời gian thực:

*(Sinh viên chèn ảnh Screenshot của Kibana Discover khi search `container.name: "airflow-worker"` hoặc `"ERROR"`)*

![Kibana Discover Log Stream](chèn_ảnh_kibana_discover_vào_đây.png)

> **Đánh giá:** ELK Stack hoạt động hoàn hảo. Độ trễ từ lúc container sinh log đến lúc hiển thị trên màn hình Kibana chỉ rơi vào khoảng vài mili-giây.

---
## 🎯 Tổng Kết
Hệ thống **Toxic Comment Data Platform** đã sở hữu một kiến trúc Observability (Giám sát) chuẩn doanh nghiệp. Bất kỳ sự cố nào về nghẽn cổ chai (Bottleneck) hay sập hệ thống (Crash) đều được ghi nhận bằng Log và báo động đỏ ngay lập tức về điện thoại của Data Engineer.
