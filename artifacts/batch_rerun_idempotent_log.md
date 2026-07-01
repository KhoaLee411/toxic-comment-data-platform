# Kiểm chứng Tính Ổn Định của Batch Job (Idempotent Test)

Trong xử lý dữ liệu Batch, một yêu cầu quan trọng là **Tính Độc Lập Kịch Bản (Idempotent)**: Việc chạy lại cùng một batch job nhiều lần không được làm nhân đôi (duplicate) hay làm sai lệch dữ liệu ở đích đến (Data Warehouse).

Dưới đây là bài test chạy lại (Rerun) job Batch lần thứ 2 liên tiếp để chứng minh điều đó.

## 1. Trạng Thái Hiện Tại (Lần chạy 1)

**Lệnh đếm số lượng:**
```bash
docker exec postgres psql -U postgres -d toxic_comment_db -c "SELECT count(*) FROM staging.batch;"
```
**Output:**
```text
 count 
-------
 10000
(1 row)
```

## 2. Rerun Batch Lần 2 Liên Tiếp

**Lệnh chạy lại:**
```bash
time python batch_processing/main.py
```

**Log Thực Thi (Spark Output):**
```text
2026-07-02 00:22:03.524 | SUCCESS  | spark_session:create_spark_session:36 - Spark session created.
2026-07-02 00:22:03.530 | INFO     | __main__:main:69 - Processing folder: text_comment_1 for batch pipeline
2026-07-02 00:22:06.730 | INFO     | __main__:main:73 - Read 10000 rows, columns: ['comment_text', 'labels']
[Stage 6:>                                                          (0 + 4) / 4]
2026-07-02 00:22:14.706 | SUCCESS  | __main__:main:97 - Successfully processed and wrote folder 'text_comment_1' to staging.
```

**Thời gian xử lý:**
```text
real	0m17.834s
user	0m3.150s
sys	0m1.033s
```
*(Spark tái khởi động và tiếp tục load, phân tích 10,000 bản ghi mới mất 17.8s)*

## 3. Kiểm Tra Dữ Liệu Sau Khi Rerun

Để xác nhận không bị Duplicate, ta chạy lại lệnh `count(*)`:

**Lệnh kiểm tra:**
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

👉 **Kết luận (Chứng minh/Loại trừ Duplicate):** 
- Số lượng dòng (row count) vẫn giữ nguyên chính xác ở mức **10000** thay vì bị đội lên thành 20000. 
- Nguyên nhân là do Code PySpark áp dụng chiến lược `mode="overwrite"`. Nó đảm bảo mỗi lần luồng Batch chạy, nó sẽ tự động dọn dẹp phân vùng cũ và nạp mới, qua đó **loại trừ hoàn toàn tình trạng Duplicate data** nếu vô tình trigger (kích hoạt) job nhiều lần trên Airflow.
