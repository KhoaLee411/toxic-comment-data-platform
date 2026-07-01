# Xử lý dữ liệu Batch (PySpark)

Tiến hành xử lý lô dữ liệu (Batch) đầu tiên. PySpark sẽ đọc dữ liệu từ Data Lake (MinIO), thực hiện Tokenize bình luận bằng model DistilBERT, và ghi kết quả dạng bảng vào `staging.batch` trên PostgreSQL.

## 1. Kiểm Tra Số Lượng Record Trước Khi Chạy

**Lệnh kiểm tra PostgreSQL:**

```bash
docker exec postgres psql -U postgres -d toxic_comment_db -c "SELECT count(*) FROM staging.batch;"
```

**Output thu được:**

```text
 count
-------
     0
(1 row)
```

## 2. Quá Trình Thực Thi Job PySpark Batch

**Lệnh đã chạy:**

```bash
time python batch_processing/main.py
```

**Log Thực Thi (Spark & System Output):**

```text
2026-07-02 00:17:54.079 | SUCCESS  | spark_session:create_spark_session:36 - Spark session created.
2026-07-02 00:17:54.079 | INFO     | minio_config:load_minio_config:13 - Applying MinIO configuration to Spark...
2026-07-02 00:17:54.083 | SUCCESS  | minio_config:load_minio_config:28 - MinIO configuration applied.
2026-07-02 00:17:54.085 | INFO     | __main__:main:69 - Processing folder: text_comment_1 for batch pipeline
2026-07-02 00:17:57.460 | INFO     | __main__:main:73 - Read 10000 rows, columns: ['comment_text', 'labels']
[Stage 4:>                                                          (0 + 1) / 1]
...
[Stage 6:>                                                          (0 + 4) / 4]
2026-07-02 00:18:06.108 | SUCCESS  | __main__:main:97 - Successfully processed and wrote folder 'text_comment_1' to staging.
```

**Thời gian xử lý:**

```text
real	0m19.365s
user	0m3.083s
sys	0m0.932s
```

_(Xử lý thành công 10,000 records từ Data Lake sang PostgreSQL, bao gồm cả chi phí Tokenize, tốn chưa tới 20 giây nhờ sức mạnh tính toán song song của Spark)._

## 3. Kiểm Tra Số Lượng Record Sau Khi Chạy

**Lệnh kiểm tra PostgreSQL:**

```bash
docker exec postgres psql -U postgres -d toxic_comment_db -c "SELECT count(*) FROM staging.batch;"
```

**Output thu được:**

```text
 count
-------
 10000
(1 row)
```

👉 **Kết luận:** Lô dữ liệu lớn đã được di chuyển thành công từ Data Lake (phi cấu trúc) qua Pipeline xử lý ngôn ngữ và hạ cánh an toàn xuống Data Warehouse (có cấu trúc).
