"""
Register stage: đọc eval_metrics.json, chỉ register lên MLflow Model Registry
nếu AUC đạt ngưỡng. Tách hoàn toàn khỏi train để có thể skip khi cần.
"""
import json
import sys

import mlflow
import mlflow.pytorch
import torch
from config import Config
from loguru import logger

from model import BertClassifier

AUC_THRESHOLD = float(Config.__dict__.get("MIN_REGISTER_AUC", 0.80))


def load_eval_metrics(path: str = "metrics/eval_metrics.json") -> dict:
    with open(path) as f:
        return json.load(f)


def load_best_model() -> BertClassifier:
    ckpt = Config.MODEL_FOLDER / "best_model.pt"
    model = BertClassifier()
    model.load_state_dict(torch.load(str(ckpt), map_location="cpu"))
    return model


def main():
    mlflow.set_tracking_uri(Config.MLFLOW_TRACKING_URI)
    mlflow.set_experiment("toxic-comment-classification")

    metrics = load_eval_metrics()
    auc = metrics.get("auc", 0.0)
    logger.info(f"Eval AUC: {auc:.4f} | Register threshold: {AUC_THRESHOLD}")

    if auc < AUC_THRESHOLD:
        logger.warning(f"AUC {auc:.4f} below threshold {AUC_THRESHOLD}. Skipping registration.")
        sys.exit(0)

    model = load_best_model()

    with mlflow.start_run(run_name="model-registration"):
        classification_report = metrics.pop("classification_report", None)
        mlflow.log_metrics(metrics)
        if classification_report:
            mlflow.log_dict(classification_report, "classification_report.json")
        from mlflow.models.signature import ModelSignature
        from mlflow.types.schema import Schema, TensorSpec
        import numpy as np

        input_schema = Schema([
            TensorSpec(np.dtype(np.int32), (-1, 512), "input_ids"),
            TensorSpec(np.dtype(np.int32), (-1, 512), "attention_mask"),
        ])
        output_schema = Schema([
            TensorSpec(np.dtype(np.float32), (-1, 1), "predictions"),
        ])
        signature = ModelSignature(inputs=input_schema, outputs=output_schema)
        
        mlflow.pytorch.log_model(
            model,
            name="model",
            registered_model_name="bert-toxic-classifier",
            signature=signature
        )
        logger.info("Model registered in MLflow as 'bert-toxic-classifier'")


if __name__ == "__main__":
    main()