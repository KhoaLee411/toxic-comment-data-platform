# Chương 5: Data Transformation (dbt)

Sau khi dữ liệu đã qua kiểm định (Data Validation) và nằm yên trong tầng Staging (gồm `staging.batch` và `staging.streaming`), chúng ta sử dụng **dbt (data build tool)** để thực hiện bước Transformation (Chuyển đổi dữ liệu). 

Mục đích của bước này là:
1. Gộp (Union) cả 2 nguồn dữ liệu (Batch và Stream).
2. Xử lý trùng lặp (Deduplication) để tránh việc một comment bị xử lý nhiều lần.
3. Chuyển dữ liệu đã được làm sạch sang tầng **Production** (`production.comments`) để sẵn sàng cho quá trình Train Model.

## 1. Thực thi dbt run và dbt test

**Lệnh thực thi:**
```bash
cd data_transformation 
set -a && source ../.env && set +a
dbt run --profiles-dir . --target prod
dbt test --profiles-dir . --target prod
```

**Log thực thi:**
```text
19:18:30  Running with dbt=1.8.2
19:18:30  Registered adapter: postgres=1.8.2
19:18:32  Found 1 model, 4 data tests, 2 sources, 428 macros
19:18:32  Concurrency: 4 threads (target='prod')
19:18:32  1 of 1 START sql table model production.comments ............................... [RUN]
19:18:32  1 of 1 OK created sql table model production.comments .......................... [SELECT 10090 in 0.33s]
19:18:32  Finished running 1 table model in 0 hours 0 minutes and 0.45 seconds (0.45s).
19:18:32  Completed successfully
19:18:32  Done. PASS=1 WARN=0 ERROR=0 SKIP=0 TOTAL=1

19:20:33  Running with dbt=1.8.2
19:20:33  Registered adapter: postgres=1.8.2
19:20:34  Found 1 model, 4 data tests, 2 sources, 428 macros
19:20:34  Concurrency: 4 threads (target='prod')
19:20:34  1 of 4 START test accepted_values_comments_labels__False__0__1 ................. [RUN]
19:20:34  2 of 4 START test not_null_comments_id ......................................... [RUN]
19:20:34  3 of 4 START test not_null_comments_labels ..................................... [RUN]
19:20:34  4 of 4 START test unique_comments_id ........................................... [RUN]
19:20:34  1 of 4 PASS accepted_values_comments_labels__False__0__1 ....................... [PASS in 0.07s]
19:20:34  2 of 4 PASS not_null_comments_id ............................................... [PASS in 0.08s]
19:20:34  3 of 4 PASS not_null_comments_labels ........................................... [PASS in 0.08s]
19:20:34  4 of 4 PASS unique_comments_id ................................................. [PASS in 0.08s]
19:20:34  Finished running 4 data tests in 0 hours 0 minutes and 0.16 seconds (0.16s).
19:20:34  Completed successfully
19:20:34  Done. PASS=4 WARN=0 ERROR=0 SKIP=0 TOTAL=4
```

## 2. Kết quả thu được

Quá trình chạy dbt đã tạo ra các file metadata (`run_results.json`, `manifest.json`) nằm trong thư mục `target/` phục vụ cho Data Lineage và Document.

Quan trọng nhất, bảng `production.comments` đã được tạo thành công với **10,090 dòng** dữ liệu. 

*(Giải thích thêm: Tổng ban đầu là 10,000 dòng batch + 94 dòng stream = 10,094 dòng. Quá trình dbt sử dụng `DISTINCT ON (id)` đã loại bỏ thành công 4 bản ghi bị trùng lặp, đảm bảo dữ liệu tinh khiết 100% trước khi đưa vào Huấn luyện mô hình).*
