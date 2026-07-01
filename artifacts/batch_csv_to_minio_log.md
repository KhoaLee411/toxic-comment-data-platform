# Xử lý Batch - Chuyển đổi CSV sang Delta và Upload lên MinIO

Minh chứng (artifacts) cho quá trình tiền xử lý dữ liệu Batch, nơi hệ thống đọc file CSV thô, chuyển đổi sang định dạng Delta Lake, và đẩy (upload) an toàn lên Data Lake (MinIO).

## 1. Log Chạy Script Convert & Upload

**Lệnh đã chạy:**

```bash
# 1. Chuyển CSV sang Delta Lake format
python utils/csv_to_delta_table.py

# 2. Upload thư mục Delta lên MinIO
python utils/upload_data_to_datalake.py
```

**Output thu được:**

```text
✅ Converted 'text_comment_2.csv' -> Delta table 'text_comment_2'
✅ Converted 'text_comment_1.csv' -> Delta table 'text_comment_1'

✅ Created bucket: raw
📤 Uploaded data_local/delta_format/text_comment_2/_delta_log/00000000000000000000.json → raw/delta_lake/text_comment_2/_delta_log/00000000000000000000.json
📤 Uploaded data_local/delta_format/text_comment_1/_delta_log/00000000000000000000.json → raw/delta_lake/text_comment_1/_delta_log/00000000000000000000.json
📤 Uploaded data_local/delta_format/text_comment_2/part-00001-4c889639-61f3-44ab-9165-161d7a842751-c000.snappy.parquet → raw/delta_lake/text_comment_2/part-00001-4c889639-61f3-44ab-9165-161d7a842751-c000.snappy.parquet
📤 Uploaded data_local/delta_format/text_comment_1/part-00001-18eda915-9c6f-435d-b35c-183f966023a0-c000.snappy.parquet → raw/delta_lake/text_comment_1/part-00001-18eda915-9c6f-435d-b35c-183f966023a0-c000.snappy.parquet
```

## 2. Kiểm Tra Trực Tiếp Trên MinIO (Data Lake)

Sử dụng MinIO Client (`mc`) bên trong container `minio` để xác minh các object đã thực sự được lưu trữ:

**Lệnh kiểm tra list object:**

```bash
docker exec minio mc alias set local_minio http://localhost:9000 admin <PASSWORD>
docker exec minio mc ls --recursive local_minio/raw/delta_lake/
```

**Kết quả (MinIO Objects Listing):**

```text
[2026-07-01 17:14:05 UTC] 1.4KiB STANDARD text_comment_1/_delta_log/00000000000000000000.json
[2026-07-01 17:14:05 UTC] 2.4MiB STANDARD text_comment_1/part-00001-18eda915-9c6f-435d-b35c-183f966023a0-c000.snappy.parquet
[2026-07-01 17:14:05 UTC] 5.8KiB STANDARD text_comment_2/_delta_log/00000000000000000000.json
[2026-07-01 17:14:05 UTC] 2.4MiB STANDARD text_comment_2/part-00001-4c889639-61f3-44ab-9165-161d7a842751-c000.snappy.parquet
```

## 3. Xác Minh Tính Toàn Vẹn Dữ Liệu (Checksum MD5)

Để chứng minh dữ liệu tải lên không bị hỏng hóc hay thay đổi (Data Integrity), ta tiến hành so sánh mã Hash MD5 của file gốc ở Local và ETag trên MinIO:

**A. Kiểm tra ETag trên MinIO:**

```bash
docker exec minio mc stat local_minio/raw/delta_lake/text_comment_1/part-00001-18eda915-9c6f-435d-b35c-183f966023a0-c000.snappy.parquet
```

_Output trích xuất:_

```yaml
Name: part-00001-18eda915-9c6f-435d-b35c-183f966023a0-c000.snappy.parquet
Size: 2.4 MiB
ETag: 385f9e27c1802af2b89bed4755642d67
```

**B. Kiểm tra MD5 của file dưới Local:**

```bash
md5sum data_local/delta_format/text_comment_1/part-00001-18eda915-9c6f-435d-b35c-183f966023a0-c000.snappy.parquet
```

_Output:_

```text
385f9e27c1802af2b89bed4755642d67  .../part-00001-18eda915-9c6f-435d-b35c-183f966023a0-c000.snappy.parquet
```

👉 **Kết luận:** Mã băm `385f9e27c1802af2b89bed4755642d67` khớp nhau hoàn toàn 100%. Quá trình upload thành công và đảm bảo tính nguyên vẹn của dữ liệu!
