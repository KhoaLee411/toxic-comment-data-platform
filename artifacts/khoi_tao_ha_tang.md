# Khởi tạo hạ tầng

Output thực tế được ghi nhận sau khi khởi chạy hạ tầng thành công.

**Lệnh đã chạy:**

```bash
docker compose -f data_lake_compose.yml -f stream_kafka_compose.yaml up -d
```

## 1. Trạng thái các Container (Docker Compose PS)

Sau khi hệ thống khởi động, tất cả các container cốt lõi đều đạt trạng thái `Up` và phần lớn vượt qua `(healthy)` check:

```text
NAME                     IMAGE                                             COMMAND                  SERVICE           CREATED         STATUS                   PORTS
minio                    minio/minio                                       "/usr/bin/docker-ent…"   minio             9 minutes ago   Up 9 minutes             0.0.0.0:9000-9001->9000-9001/tcp, [::]:9000-9001->9000-9001/tcp
postgres                 postgres:16                                       "docker-entrypoint.s…"   postgres          9 minutes ago   Up 9 minutes (healthy)   0.0.0.0:5433->5432/tcp, [::]:5433->5432/tcp
stream-broker            confluentinc/cp-server:7.5.0                      "/etc/confluent/dock…"   broker            5 minutes ago   Up 5 minutes (healthy)   0.0.0.0:9092->9092/tcp, [::]:9092->9092/tcp
stream-control-center    confluentinc/cp-enterprise-control-center:7.5.0   "/etc/confluent/dock…"   control-center    5 minutes ago   Up 5 minutes             0.0.0.0:9021->9021/tcp, [::]:9021->9021/tcp
stream-debezium          toxic-comment-data-platform-debezium              "/docker-entrypoint.…"   debezium          5 minutes ago   Up 5 minutes (healthy)   0.0.0.0:8083->8083/tcp, [::]:8083->8083/tcp, 9092/tcp
stream-debezium-ui       debezium/debezium-ui:latest                       "/deployments/run-ja…"   debezium-ui       5 minutes ago   Up 5 minutes             0.0.0.0:8085->8080/tcp, [::]:8085->8080/tcp
stream-schema-registry   confluentinc/cp-schema-registry:7.5.0             "/etc/confluent/dock…"   schema-registry   5 minutes ago   Up 5 minutes (healthy)   0.0.0.0:8081->8081/tcp, [::]:8081->8081/tcp
stream-zookeeper         confluentinc/cp-zookeeper:7.5.0                   "/etc/confluent/dock…"   zookeeper         5 minutes ago   Up 5 minutes (healthy)   2888/tcp, 0.0.0.0:2181->2181/tcp, [::]:2181->2181/tcp, 3888/tcp
```

## 2. Chi tiết Healthcheck Logs

Trích xuất log kiểm tra sức khỏe (Healthcheck) của các component quan trọng nhất, chứng minh chúng đang hoạt động ổn định và sẵn sàng nhận kết nối:

### PostgreSQL

```json
{
  "Start": "2026-07-01T23:47:06.859628302+07:00",
  "End": "2026-07-01T23:47:06.943385806+07:00",
  "ExitCode": 0,
  "Output": "/var/run/postgresql:5432 - accepting connections\n"
}
```

### Kafka Broker

```json
{
  "Start": "2026-07-01T23:47:06.06759166+07:00",
  "End": "2026-07-01T23:47:06.118581667+07:00",
  "ExitCode": 0,
  "Output": ""
}
```

### Zookeeper

```json
{
  "Start": "2026-07-01T23:47:03.553349859+07:00",
  "End": "2026-07-01T23:47:03.616573267+07:00",
  "ExitCode": 0,
  "Output": "Zookeeper version: 3.6.4--d65253dcf68e9097c6e95a126463fd5fdeb4521c, built on 12/18/2022 18:10 GMT\nLatency min/avg/max: 0/0.5182/21\nReceived: 2063\nSent: 2122\nConnections: 2\nOutstanding: 0\nZxid: 0x25f\nMode: standalone\nNode count: 538\n"
}
```

### Debezium (CDC)

```json
{
  "Start": "2026-07-01T23:47:04.770530428+07:00",
  "End": "2026-07-01T23:47:04.819253473+07:00",
  "ExitCode": 0,
  "Output": "[]"
}
```

### Schema Registry

```json
{
  "Start": "2026-07-01T23:47:09.586015927+07:00",
  "End": "2026-07-01T23:47:09.657802784+07:00",
  "ExitCode": 0,
  "Output": ""
}
```
