# Chương 6: Huấn luyện và Đánh giá Mô hình (DVC & MLFlow)

Sau khi dữ liệu đã được làm sạch và lưu tại `production.comments`, chúng ta sử dụng **DVC (Data Version Control)** để quản lý quy trình huấn luyện mô hình (ML Pipeline) và **MLFlow** để tracking các thử nghiệm.

## 1. Kích hoạt DVC Pipeline

Toàn bộ quy trình (Extract data -> Train -> Evaluate -> Register Model) được định nghĩa trong `dvc.yaml` và được chạy thông qua lệnh duy nhất:

```bash
set -a && source .env && set +a
dvc repro
```

**Log thực thi của DVC:**
```text
Running stage 'extract':
> python model_experiment/extract_data.py
2026-07-02 02:23:57.129 | INFO | 🔌 Using PostgreSQL host: localhost
✅ Data exported to data_local/production/cleaned_data.csv
Updating lock file 'dvc.lock'

Running stage 'train':
> python model_experiment/train.py
2026-07-02 02:24:03.843 | INFO | Device: cpu
2026-07-02 02:24:36.164 | INFO | [Epoch 1 | Step 1/1] Loss: 0.6931
2026-07-02 02:24:40.210 | INFO | ✅ Best model saved at: model_checkpoints/best_model.pt
Updating lock file 'dvc.lock'

Running stage 'evaluate':
> python model_experiment/evaluate.py
2026-07-02 02:24:42.500 | INFO | Device: cpu
2026-07-02 02:24:43.100 | INFO | ✅ Evaluation Metrics saved to metrics/eval_metrics.json
Updating lock file 'dvc.lock'

Running stage 'register':
> python model_experiment/register_model.py
2026-07-02 02:24:45.095 | INFO | Eval AUC: 0.3200 | Register threshold: 0.8
2026-07-02 02:24:45.095 | WARNING | AUC 0.3200 below threshold 0.8. Skipping registration.
Updating lock file 'dvc.lock'
```

## 2. Kết quả Metrics (Thước đo Đánh giá)

Sau khi pipeline hoàn tất, các chỉ số đánh giá được ghi lại chi tiết vào thư mục `metrics/`.

### 2.1. Train Metrics (`metrics/train_metrics.json`)
```json
{
  "best_val_auc": 0.32,
  "epochs": 1
}
```

### 2.2. Evaluate Metrics (`metrics/eval_metrics.json`)
```json
{
  "auc": 0.32,
  "f1": 0.0,
  "accuracy": 0.6667,
  "threshold": 0.45,
  "classification_report": {
    "0": {
      "precision": 0.6666,
      "recall": 1.0,
      "f1-score": 0.8,
      "support": 10.0
    },
    "1": {
      "precision": 0.0,
      "recall": 0.0,
      "f1-score": 0.0,
      "support": 5.0
    }
  }
}
```

## 3. Tổng kết Pipeline

- **File Track:** DVC đã sinh ra file `dvc.lock` dùng để khóa phiên bản dữ liệu và mã nguồn, đảm bảo tính tái lập (Reproducibility).
- **Checkpoints:** Mô hình tốt nhất (Best Model) đã được lưu thành công tại `model_checkpoints/best_model.pt`.
- **Đăng ký mô hình:** Vì điểm số AUC hiện tại (`0.32`) chưa vượt qua ngưỡng cấu hình (`0.8`), mô hình sẽ không tự động được đăng ký (Register) lên MLFlow Model Registry. *(Để nâng cao độ chính xác, chúng ta sẽ cần train với nhiều epoch hơn hoặc đổi mô hình mạnh hơn).*
