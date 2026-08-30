"""Train and export the production BloomAI flower classifier."""

from __future__ import annotations

import argparse
import json
import random
from pathlib import Path

import numpy as np
import torch
from torch import nn
from torch.optim import AdamW
from torch.optim.lr_scheduler import ReduceLROnPlateau
from torch.utils.data import DataLoader
from torchvision import datasets, transforms

from modeling import (
    IMAGENET_MEAN,
    IMAGENET_STD,
    build_model,
    load_labels,
    save_artifact,
)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Train MobileNetV3-Small on Oxford Flowers 102")
    parser.add_argument("data_dir", type=Path, help="Directory containing train, valid, and test")
    parser.add_argument("--labels", type=Path, default=Path("data/flower_labels.json"))
    parser.add_argument("--output", type=Path, default=Path("models/mobilenet_v3_small_flowers102.pth"))
    parser.add_argument("--metrics-output", type=Path, default=Path("models/metrics.json"))
    parser.add_argument("--epochs", type=int, default=20)
    parser.add_argument("--frozen-epochs", type=int, default=3)
    parser.add_argument("--batch-size", type=int, default=64)
    parser.add_argument("--learning-rate", type=float, default=3e-4)
    parser.add_argument("--fine-tune-learning-rate", type=float, default=3e-5)
    parser.add_argument("--weight-decay", type=float, default=1e-4)
    parser.add_argument("--patience", type=int, default=5)
    parser.add_argument("--workers", type=int, default=2)
    parser.add_argument("--seed", type=int, default=42)
    return parser.parse_args()


def seed_everything(seed: int) -> None:
    random.seed(seed)
    np.random.seed(seed)
    torch.manual_seed(seed)
    if torch.cuda.is_available():
        torch.cuda.manual_seed_all(seed)
    torch.backends.cudnn.deterministic = True
    torch.backends.cudnn.benchmark = False


def loaders(data_dir: Path, batch_size: int, workers: int) -> tuple[dict[str, datasets.ImageFolder], dict[str, DataLoader]]:
    train_transform = transforms.Compose(
        [
            transforms.RandomResizedCrop(224, scale=(0.7, 1.0)),
            transforms.RandomHorizontalFlip(),
            transforms.RandomRotation(15),
            transforms.ColorJitter(brightness=0.2, contrast=0.2, saturation=0.2),
            transforms.ToTensor(),
            transforms.Normalize(IMAGENET_MEAN, IMAGENET_STD),
        ]
    )
    evaluation_transform = transforms.Compose(
        [
            transforms.Resize(256),
            transforms.CenterCrop(224),
            transforms.ToTensor(),
            transforms.Normalize(IMAGENET_MEAN, IMAGENET_STD),
        ]
    )
    transforms_by_split = {
        "train": train_transform,
        "valid": evaluation_transform,
        "test": evaluation_transform,
    }
    data = {
        split: datasets.ImageFolder(data_dir / split, transform=transform)
        for split, transform in transforms_by_split.items()
    }
    if any(len(dataset.classes) != 102 for dataset in data.values()):
        raise ValueError("Every dataset split must contain exactly 102 categories")
    if any(dataset.class_to_idx != data["train"].class_to_idx for dataset in data.values()):
        raise ValueError("Class mappings differ between train, validation, and test splits")
    pin_memory = torch.cuda.is_available()
    result = {
        split: DataLoader(
            dataset,
            batch_size=batch_size,
            shuffle=split == "train",
            num_workers=workers,
            pin_memory=pin_memory,
            persistent_workers=workers > 0,
        )
        for split, dataset in data.items()
    }
    return data, result


def run_epoch(model, loader, criterion, device, optimizer=None) -> tuple[float, float, float]:
    training = optimizer is not None
    model.train(training)
    total_loss = total_correct = total_top5 = total = 0
    amp_enabled = device.type == "cuda"
    for inputs, targets in loader:
        inputs, targets = inputs.to(device), targets.to(device)
        if training:
            optimizer.zero_grad(set_to_none=True)
        with torch.amp.autocast(device_type=device.type, enabled=amp_enabled):
            logits = model(inputs)
            loss = criterion(logits, targets)
        if training:
            loss.backward()
            nn.utils.clip_grad_norm_(model.parameters(), max_norm=1.0)
            optimizer.step()
        batch = targets.size(0)
        total += batch
        total_loss += loss.item() * batch
        total_correct += (logits.argmax(dim=1) == targets).sum().item()
        total_top5 += logits.topk(5, dim=1).indices.eq(targets[:, None]).any(dim=1).sum().item()
    return total_loss / total, total_correct / total, total_top5 / total


def main() -> None:
    args = parse_args()
    if args.frozen_epochs < 0 or args.frozen_epochs >= args.epochs:
        raise ValueError("frozen-epochs must be non-negative and smaller than epochs")
    seed_everything(args.seed)
    device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
    labels = load_labels(args.labels)
    datasets_by_split, data_loaders = loaders(args.data_dir, args.batch_size, args.workers)
    model = build_model(pretrained=True).to(device)
    for parameter in model.features.parameters():
        parameter.requires_grad = False
    criterion = nn.CrossEntropyLoss(label_smoothing=0.1)
    optimizer = AdamW(model.classifier.parameters(), lr=args.learning_rate, weight_decay=args.weight_decay)
    scheduler = ReduceLROnPlateau(optimizer, mode="max", factor=0.3, patience=2)
    best_state = None
    best_accuracy = -1.0
    epochs_without_improvement = 0
    history = []

    for epoch in range(args.epochs):
        if epoch == args.frozen_epochs:
            for parameter in model.features.parameters():
                parameter.requires_grad = True
            optimizer = AdamW(model.parameters(), lr=args.fine_tune_learning_rate, weight_decay=args.weight_decay)
            scheduler = ReduceLROnPlateau(optimizer, mode="max", factor=0.3, patience=2)
        train_loss, train_accuracy, _ = run_epoch(model, data_loaders["train"], criterion, device, optimizer)
        with torch.inference_mode():
            valid_loss, valid_accuracy, valid_top5 = run_epoch(model, data_loaders["valid"], criterion, device)
        scheduler.step(valid_accuracy)
        record = {
            "epoch": epoch + 1,
            "train_loss": train_loss,
            "train_accuracy": train_accuracy,
            "validation_loss": valid_loss,
            "validation_accuracy": valid_accuracy,
            "validation_top5_accuracy": valid_top5,
        }
        history.append(record)
        print(json.dumps(record))
        if valid_accuracy > best_accuracy:
            best_accuracy = valid_accuracy
            best_state = {key: value.detach().cpu().clone() for key, value in model.state_dict().items()}
            epochs_without_improvement = 0
        else:
            epochs_without_improvement += 1
            if epochs_without_improvement >= args.patience:
                break

    if best_state is None:
        raise RuntimeError("Training did not produce a checkpoint")
    model.load_state_dict(best_state)
    model.to(device).eval()
    with torch.inference_mode():
        test_loss, test_accuracy, test_top5 = run_epoch(model, data_loaders["test"], criterion, device)
    metrics = {
        "best_validation_accuracy": best_accuracy,
        "test_loss": test_loss,
        "test_accuracy": test_accuracy,
        "test_top5_accuracy": test_top5,
    }
    save_artifact(args.output, model, datasets_by_split["train"].class_to_idx, labels, metrics)
    args.metrics_output.parent.mkdir(parents=True, exist_ok=True)
    args.metrics_output.write_text(json.dumps({"metrics": metrics, "history": history}, indent=2), encoding="utf-8")
    print(json.dumps({"artifact": str(args.output), **metrics}))


if __name__ == "__main__":
    main()
