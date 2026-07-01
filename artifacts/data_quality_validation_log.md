# Chương 5: Đảm bảo Chất lượng Dữ liệu (Data Quality Validation)

Sau khi dữ liệu từ luồng Batch và luồng Stream đều đã hạ cánh xuống Data Warehouse, chúng ta áp dụng thư viện **Great Expectations (GX)** để kiểm định chất lượng dữ liệu (Data Quality). Việc này giúp đảm bảo dữ liệu không bị lỗi null, sai format hoặc vi phạm các ràng buộc nghiệp vụ (Data Contracts).

## 1. Thực Thi Quá Trình Validate

Script sẽ tự động cắm vào PostgreSQL và chạy qua toàn bộ các bảng staging (`batch` và `streaming`) để kiểm tra.

**Lệnh thực thi:**
```bash
python data_validation/validate.py --source all
```

**Output Console thu được:**
```text
=== Validating PostgreSQL batch source (batch) ===
Calculating Metrics: 100%|████████████████████| 10/10 [00:00<00:00, 1501.77it/s]
...
Calculating Metrics: 100%|████████████████████| 46/46 [00:00<00:00, 2123.91it/s]

=== Validating PostgreSQL stream source (staging.streaming) ===
Calculating Metrics: 100%|████████████████████| 10/10 [00:00<00:00, 1501.77it/s]
...
Calculating Metrics: 100%|████████████████████| 46/46 [00:00<00:00, 2123.91it/s]

=== Validation Summary ===
PASSED
```

## 2. Kết Quả Báo Cáo (Data Docs HTML & JSON)

Sau khi kiểm định thành công (PASSED), Great Expectations tự động sinh ra các báo cáo dạng giao diện Web (Data Docs) và JSON Validation Result:

- **Báo cáo HTML (Data Docs):** Cung cấp giao diện trực quan cho người dùng cuối (Business/Data Analyst) xem kết quả.
  *Đường dẫn sinh ra: `data_validation/gx/uncommitted/data_docs/local_site/index.html`*
- **Validation Result (JSON):** Chứa các metadata (ví dụ: pass/fail, observed value) dành cho các hệ thống tự động hóa CI/CD đọc và cảnh báo.

👉 **Kết luận:** Dữ liệu trong Data Warehouse hoàn toàn **Sạch (Clean)** và tuân thủ các quy tắc dữ liệu đã định sẵn, sẵn sàng đưa vào các công đoạn Phân tích hoặc Train Model tiếp theo.
