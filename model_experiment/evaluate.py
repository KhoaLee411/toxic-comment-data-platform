"""
Evaluate stage: load best checkpoint, compute final metrics, export to metrics/eval_metrics.json.
Chạy sau train stage trong DVC pipeline.
"""
import json
import os

import torch
from config import Config
from dataloader import val_dataloader
from loguru import logger
from sklearn.metrics import (
    accuracy_score,
    classification_report,
    f1_score,
    roc_auc_score,
)

from model import BertClassifier

device = Config.DEVICE


def load_best_model() -> BertClassifier:
    best_ckpt = Config.MODEL_FOLDER / "best_model.pt"
    if not best_ckpt.exists():
        raise FileNotFoundError(f"best_model.pt not found in {Config.MODEL_FOLDER}. Run train stage first.")
    model = BertClassifier().to(device)
    model.load_state_dict(torch.load(str(best_ckpt), map_location=device))
    model.eval()
    logger.info(f"Loaded checkpoint: {best_ckpt}")
    return model


def run_evaluation(model: BertClassifier) -> dict:
    labels_all, preds_all, scores_all = [], [], []
    with torch.no_grad():
        for batch in val_dataloader:
            input_ids = batch["input_ids"].to(device)
            attention_mask = batch["attention_mask"].to(device)
            labels = batch["labels"].unsqueeze(1)

            scores = torch.sigmoid(model(input_ids, attention_mask))
            preds = (scores > Config.TOXIC_THRESHOLD).int()

            scores_all.extend(scores.cpu().numpy().flatten())
            preds_all.extend(preds.cpu().numpy().flatten())
            labels_all.extend(labels.cpu().numpy().flatten())

    auc = roc_auc_score(labels_all, scores_all)
    f1 = f1_score(labels_all, preds_all)
    acc = accuracy_score(labels_all, preds_all)
    report = classification_report(labels_all, preds_all, output_dict=True)

    logger.info(f"AUC: {auc:.4f} | F1: {f1:.4f} | Accuracy: {acc:.4f}")
    return {
        "auc": round(auc, 4),
        "f1": round(f1, 4),
        "accuracy": round(acc, 4),
        "threshold": Config.TOXIC_THRESHOLD,
        "classification_report": report,
    }


def main():
    os.makedirs("metrics", exist_ok=True)
    model = load_best_model()
    metrics = run_evaluation(model)

    out_path = "metrics/eval_metrics.json"
    with open(out_path, "w") as f:
        json.dump(metrics, f, indent=2)
    logger.info(f"Eval metrics saved to {out_path}")


if __name__ == "__main__":
    main()