import json
import os

import mlflow
import torch
from config import Config
from dataloader import train_dataloader, val_dataloader
from loguru import logger
from sklearn.metrics import roc_auc_score
from torch import nn, optim

from model import BertClassifier

# ── MLflow setup ──────────────────────────────────────────────────────────────
mlflow.set_tracking_uri(Config.MLFLOW_TRACKING_URI)
mlflow.set_experiment("toxic-comment-classification")

device = Config.DEVICE
logger.info(f"Device: {device}")


def freeze_bert_layers(model: BertClassifier) -> None:
    for param in model.parameters():
        param.requires_grad = False
    for param in model.linear1.parameters():
        param.requires_grad = True
    for param in model.linear2.parameters():
        param.requires_grad = True


def train_one_epoch(model, loader, optimizer, loss_fn, epoch: int) -> float:
    model.train()
    total_loss = 0.0
    for step, batch in enumerate(loader, start=1):
        optimizer.zero_grad()
        input_ids = batch["input_ids"].to(device)
        attention_mask = batch["attention_mask"].to(device)
        labels = batch["labels"].unsqueeze(1).float().to(device)

        loss = loss_fn(model(input_ids, attention_mask), labels)
        loss.backward()
        optimizer.step()
        total_loss += loss.item()

        if step % 10 == 0 or step == len(loader):
            logger.info(f"[Epoch {epoch} | Step {step}/{len(loader)}] Loss: {loss.item():.4f}")

    return total_loss / len(loader)


def validate(model, loader) -> tuple[float, float]:
    model.eval()
    labels_all, scores_all = [], []
    with torch.no_grad():
        for batch in loader:
            input_ids = batch["input_ids"].to(device)
            attention_mask = batch["attention_mask"].to(device)
            labels = batch["labels"].unsqueeze(1)

            scores = torch.sigmoid(model(input_ids, attention_mask))
            scores_all.extend(scores.cpu().numpy().flatten())
            labels_all.extend(labels.cpu().numpy())

    auc = roc_auc_score(labels_all, scores_all)
    return auc, scores_all


def main():
    classifier = BertClassifier().to(device)
    freeze_bert_layers(classifier)

    optimizer = optim.Adam([
        {"params": classifier.linear1.parameters(), "lr": 5e-4},
        {"params": classifier.linear2.parameters(), "lr": 1e-5},
    ])
    loss_fn = nn.BCEWithLogitsLoss()

    os.makedirs("metrics", exist_ok=True)
    os.makedirs(str(Config.MODEL_FOLDER), exist_ok=True)

    with mlflow.start_run():
        mlflow.log_params({
            "epochs": Config.TRAIN_EPOCHS,
            "lr_linear1": 5e-4,
            "lr_linear2": 1e-5,
            "threshold": Config.TOXIC_THRESHOLD,
            "batch_size": Config.BATCH_SIZE,
        })

        best_auc = 0.0
        for epoch in range(1, Config.TRAIN_EPOCHS + 1):
            avg_loss = train_one_epoch(classifier, train_dataloader, optimizer, loss_fn, epoch)
            auc, _ = validate(classifier, val_dataloader)

            mlflow.log_metrics({"avg_train_loss": avg_loss, "val_auc": auc}, step=epoch)
            logger.info(f"[Epoch {epoch}] Loss: {avg_loss:.4f} | Val AUC: {auc:.4f}")

            ckpt_path = str(Config.MODEL_FOLDER / f"checkpoint_epoch{epoch}.pt")
            torch.save(classifier.state_dict(), ckpt_path)
            mlflow.log_artifact(ckpt_path, artifact_path="checkpoints")

            if auc > best_auc:
                best_auc = auc
                torch.save(classifier.state_dict(), str(Config.MODEL_FOLDER / "best_model.pt"))

        # Export metrics for DVC tracking
        metrics = {"best_val_auc": best_auc, "epochs": Config.TRAIN_EPOCHS}
        with open("metrics/train_metrics.json", "w") as f:
            json.dump(metrics, f, indent=2)

        logger.info(f"Training done. Best AUC: {best_auc:.4f}")


if __name__ == "__main__":
    main()