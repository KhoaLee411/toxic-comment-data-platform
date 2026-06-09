## 2. Stream Processing with Apache Flink
### 2.1 Start Services
```shell
docker compose -f kafka-debezium-docker-compose.yaml up -d
```
### 2.2 Register Connectors
Connect `Debezium` with `PostgreSQL` to capture Change Data Capture (CDC) events:
```shell
cd debezium/
bash run.sh register_connector configs/postgresql-cdc.json
```
Access Debezium UI at `http://localhost:8085/`.

### 2.3 Initialize the Database
Periodically insert new records into the target table:
```shell
python utils/streaming_data_to_postgresql.py
```

Access the `Control Center` at `http://localhost:9021/` to monitor incoming records.

### 2.4 Run Stream Processing
```shell
python stream_processing/main.py
```

![](gifs/2.gif)