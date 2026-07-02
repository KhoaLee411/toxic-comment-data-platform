# Báo cáo: Kết quả MLFlow Tracking và Registry

Sau khi hoàn tất toàn bộ pipeline của DVC, **MLFlow** đã ghi nhận và quản lý cực kỳ chi tiết từng thông số, thước đo và cả phiên bản mô hình của chúng ta. Dưới đây là dữ liệu được trích xuất trực tiếp từ hệ thống MLFlow Tracking và Model Registry.

## 1. Thông tin Experiment

- **Tên Experiment:** `toxic-comment-classification`
- **Trạng thái:** Hoạt động bình thường.
- **Thư mục Tracking gốc:** `./mlruns`

## 2. Kết quả Quá trình Huấn luyện (Train Run)

Quá trình `train.py` đã tạo ra một Run để ghi nhận các tham số siêu tham số (Hyperparameters) và metrics trong lúc train.

- **Run ID:** `088de115c3024655b402f6c4d148f094`
- **Tên Run (Auto-generated):** `intrigued-tern-614`

**🔹 Tham số mô hình (Parameters):**
| Tham số | Giá trị | Ý nghĩa |
|---|---|---|
| `batch_size` | 64 | Kích thước lô huấn luyện. |
| `epochs` | 1 | Số vòng lặp huấn luyện. |
| `lr_linear1` | 0.0005 | Tốc độ học (Learning Rate) của lớp tuyến tính 1. |
| `lr_linear2` | 1e-05 | Tốc độ học (Learning Rate) của lớp tuyến tính 2. |
| `threshold` | 0.45 | Ngưỡng ra quyết định phân loại độc hại (Toxic threshold). |

**🔹 Chỉ số đánh giá (Metrics):**
| Chỉ số (Metric) | Giá trị |
|---|---|
| `avg_train_loss` | 0.2147 |
| `val_auc` | 0.9488 |

---

## 3. Kết quả Quá trình Đăng ký (Register Run)

Quá trình `register_model.py` đã lấy dữ liệu đánh giá từ `eval_metrics.json` và tạo một Run riêng biệt chuyên biệt cho việc Register model.

- **Run ID:** `96a5cb951f094c18b022ab34a32efa7a`
- **Tên Run:** `model-registration`

**🔹 Chỉ số đánh giá khi Evaluate (Metrics):**
| Chỉ số (Metric) | Giá trị |
|---|---|
| `auc` | 0.9488 |
| `accuracy` | 0.9432 |
| `f1` | 0.6245 |
| `threshold` | 0.45 |

*(Kèm theo bảng phân loại Classification Report đầy đủ trong file JSON của Run).*

---

## 4. Quản lý Phiên bản Mô hình (Model Registry)

Bởi vì điểm số AUC `0.9488` đã xuất sắc vượt qua ngưỡng yêu cầu `0.80`, mô hình đã được cấp phép đăng ký thành công vào hệ thống.

- **Tên Mô hình:** `bert-toxic-classifier`
- **Phiên bản mới nhất:** `Version 3`
- **Trạng thái (Status):** `READY`

### Chú thích về Model Registry:
Mô hình `bert-toxic-classifier` hiện đang ở phiên bản thứ 3 (Version 3) trong Registry. MLFlow đã đóng gói toàn bộ trọng số (Weights), môi trường Conda, và định dạng Input Signature. Model này hiện đã ở trạng thái **READY**, sẵn sàng để được hệ thống Load phục vụ Inference (Dự đoán) hoặc API Serving ngay lập tức.
