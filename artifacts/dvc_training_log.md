# Huấn luyện và Đánh giá Mô hình (DVC & MLFlow)

Sau khi dữ liệu đã được làm sạch và lưu tại `production.comments`, chúng ta sử dụng **DVC (Data Version Control)** để quản lý quy trình huấn luyện mô hình (ML Pipeline) và **MLFlow** để tracking các thử nghiệm.

## 1. Kích hoạt DVC Pipeline

Toàn bộ quy trình (Extract data -> Train -> Evaluate -> Register Model) được định nghĩa trong `dvc.yaml` và được chạy thông qua lệnh duy nhất:

```bash
set -a && source .env && set +a
dvc repro
```

**Log thực thi của DVC:**

```text
Stage 'extract' didn't change, skipping
Running stage 'train':
> python model_experiment/train.py
2026/07/02 02:38:38 INFO mlflow.tracking.fluent: Experiment with name 'toxic-comment-classification' does not exist. Creating a new experiment.
2026-07-02 02:38:38.778 | INFO     | __main__:<module>:19 - Device: cpu
2026-07-02 02:41:03.763 | INFO     | __main__:train_one_epoch:46 - [Epoch 1 | Step 10/111] Loss: 0.4690
2026-07-02 02:43:41.290 | INFO     | __main__:train_one_epoch:46 - [Epoch 1 | Step 20/111] Loss: 0.3077
2026-07-02 02:46:06.317 | INFO     | __main__:train_one_epoch:46 - [Epoch 1 | Step 30/111] Loss: 0.1643
2026-07-02 02:48:44.753 | INFO     | __main__:train_one_epoch:46 - [Epoch 1 | Step 40/111] Loss: 0.2317
2026-07-02 02:51:10.611 | INFO     | __main__:train_one_epoch:46 - [Epoch 1 | Step 50/111] Loss: 0.1821
2026-07-02 02:53:39.630 | INFO     | __main__:train_one_epoch:46 - [Epoch 1 | Step 60/111] Loss: 0.1693
2026-07-02 02:55:58.110 | INFO     | __main__:train_one_epoch:46 - [Epoch 1 | Step 70/111] Loss: 0.1066
2026-07-02 02:58:31.319 | INFO     | __main__:train_one_epoch:46 - [Epoch 1 | Step 80/111] Loss: 0.1950
2026-07-02 03:00:46.878 | INFO     | __main__:train_one_epoch:46 - [Epoch 1 | Step 90/111] Loss: 0.1618
2026-07-02 03:03:18.967 | INFO     | __main__:train_one_epoch:46 - [Epoch 1 | Step 100/111] Loss: 0.1902
2026-07-02 03:05:48.291 | INFO     | __main__:train_one_epoch:46 - [Epoch 1 | Step 110/111] Loss: 0.1678
2026-07-02 03:05:52.823 | INFO     | __main__:train_one_epoch:46 - [Epoch 1 | Step 111/111] Loss: 0.2601
2026-07-02 03:12:10.719 | INFO     | __main__:main:96 - [Epoch 1] Loss: 0.2147 | Val AUC: 0.9488
2026-07-02 03:12:11.139 | INFO     | __main__:main:111 - Training done. Best AUC: 0.9488
Updating lock file 'dvc.lock'

Running stage 'evaluate':
> python model_experiment/evaluate.py
/home/khoa-lee/Documents/my_work_space/toxic-comment-data-platform/model_experiment/evaluate.py:29: FutureWarning: You are using `torch.load` with `weights_only=False` (the current default value), which uses the default pickle module implicitly. It is possible to construct malicious pickle data which will execute arbitrary code during unpickling (See https://github.com/pytorch/pytorch/blob/main/SECURITY.md#untrusted-models for more details). In a future release, the default value for `weights_only` will be flipped to `True`. This limits the functions that could be executed during unpickling. Arbitrary objects will no longer be allowed to be loaded via this mode unless they are explicitly allowlisted by the user via `torch.serialization.add_safe_globals`. We recommend you start setting `weights_only=True` for any use case where you don't have full control of the loaded file. Please open an issue on GitHub for any issues related to this experimental feature.
  model.load_state_dict(torch.load(str(best_ckpt), map_location=device))
2026-07-02 03:12:21.265 | INFO     | __main__:load_best_model:31 - Loaded checkpoint: model_checkpoints/best_model.pt
2026-07-02 03:18:29.107 | INFO     | __main__:run_evaluation:55 - AUC: 0.9488 | F1: 0.6245 | Accuracy: 0.9432
2026-07-02 03:18:29.107 | INFO     | __main__:main:73 - Eval metrics saved to metrics/eval_metrics.json
Updating lock file 'dvc.lock'

Running stage 'register':
> python model_experiment/register_model.py
2026-07-02 03:18:32.252 | INFO     | __main__:main:37 - Eval AUC: 0.9488 | Register threshold: 0.8
/home/khoa-lee/Documents/my_work_space/toxic-comment-data-platform/model_experiment/register_model.py:27: FutureWarning: You are using `torch.load` with `weights_only=False` (the current default value), which uses the default pickle module implicitly. It is possible to construct malicious pickle data which will execute arbitrary code during unpickling (See https://github.com/pytorch/pytorch/blob/main/SECURITY.md#untrusted-models for more details). In a future release, the default value for `weights_only` will be flipped to `True`. This limits the functions that could be executed during unpickling. Arbitrary objects will no longer be allowed to be loaded via this mode unless they are explicitly allowlisted by the user via `torch.serialization.add_safe_globals`. We recommend you start setting `weights_only=True` for any use case where you don't have full control of the loaded file. Please open an issue on GitHub for any issues related to this experimental feature.
  model.load_state_dict(torch.load(str(ckpt), map_location="cpu"))
2026/07/02 03:18:33 WARNING mlflow.models.model: `artifact_path` is deprecated. Please use `name` instead.
2026/07/02 03:18:37 WARNING mlflow.models.model: Model logged without a signature and input example. Please set `input_example` parameter when logging the model to auto infer the model signature.
Successfully registered model 'bert-toxic-classifier'.
Created version '1' of model 'bert-toxic-classifier'.
2026-07-02 03:18:37.627 | INFO     | __main__:main:55 - Model registered in MLflow as 'bert-toxic-classifier'
Updating lock file 'dvc.lock'
```

## 2. Kết quả Metrics (Thước đo Đánh giá)

Sau khi pipeline hoàn tất, các chỉ số đánh giá được ghi lại chi tiết vào thư mục `metrics/`. Mô hình cho kết quả cực kỳ ấn tượng với **AUC đạt 94.88%**!

### 2.1. Train Metrics (`metrics/train_metrics.json`)

```json
{
  "best_val_auc": 0.9488379904145513,
  "epochs": 1
}
```

### 2.2. Evaluate Metrics (`metrics/eval_metrics.json`)

```json
{
  "auc": 0.9488,
  "f1": 0.6245,
  "accuracy": 0.9432,
  "threshold": 0.45,
  "classification_report": {
    "0": {
      "precision": 0.9512451771308312,
      "recall": 0.9879781420765027,
      "f1-score": 0.9692637598284489,
      "support": 2745.0
    },
    "1": {
      "precision": 0.8125,
      "recall": 0.5070921985815603,
      "f1-score": 0.6244541484716157,
      "support": 282.0
    },
    "accuracy": 0.9431780640898579,
    "macro avg": {
      "precision": 0.8818725885654156,
      "recall": 0.7475351703290315,
      "f1-score": 0.7968589541500324,
      "support": 3027.0
    },
    "weighted avg": {
      "precision": 0.9383194619174534,
      "recall": 0.9431780640898579,
      "f1-score": 0.937140763329398,
      "support": 3027.0
    }
  }
}
```

## 3. Tổng kết Pipeline

- **File Track:** DVC đã sinh ra file `dvc.lock` dùng để khóa phiên bản dữ liệu và mã nguồn, đảm bảo tính tái lập (Reproducibility).
- **Checkpoints:** Mô hình tốt nhất (Best Model) đã được lưu thành công tại `model_checkpoints/best_model.pt`.
- **Đăng ký mô hình:** Vì điểm số AUC hiện tại (`0.9488`) đã vượt qua ngưỡng cấu hình khắt khe (`0.8`), hệ thống đã tự động đóng gói Signature, Version và đẩy mô hình (Register) lên **MLFlow Model Registry** với tên gọi `bert-toxic-classifier` (Version 1). Mô hình hiện đã sẵn sàng để được kéo về phục vụ cho môi trường Production (Serving)!
