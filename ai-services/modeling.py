"""Shared MobileNetV3 model and artifact helpers for BloomAI."""

from __future__ import annotations

import json
from pathlib import Path

import torch
from torch import nn
from torchvision import models, transforms

ARCHITECTURE = "mobilenet_v3_small"
NUM_CLASSES = 102
INPUT_SIZE = 224
IMAGENET_MEAN = [0.485, 0.456, 0.406]
IMAGENET_STD = [0.229, 0.224, 0.225]


def build_model(num_classes: int = NUM_CLASSES, *, pretrained: bool = False) -> nn.Module:
    weights = models.MobileNet_V3_Small_Weights.DEFAULT if pretrained else None
    model = models.mobilenet_v3_small(weights=weights)
    in_features = model.classifier[-1].in_features
    model.classifier[-1] = nn.Linear(in_features, num_classes)
    return model


def inference_transform() -> transforms.Compose:
    return transforms.Compose(
        [
            transforms.Resize(256),
            transforms.CenterCrop(INPUT_SIZE),
            transforms.ToTensor(),
            transforms.Normalize(IMAGENET_MEAN, IMAGENET_STD),
        ]
    )


def load_labels(path: str | Path) -> dict[str, str]:
    with Path(path).open(encoding="utf-8") as handle:
        labels = json.load(handle)
    if set(labels) != {str(index) for index in range(1, NUM_CLASSES + 1)}:
        raise ValueError("Flower label mapping must contain category IDs 1 through 102")
    return labels


def category_order(class_to_idx: dict[str, int]) -> list[str]:
    ordered = [name for name, _ in sorted(class_to_idx.items(), key=lambda item: item[1])]
    if len(ordered) != NUM_CLASSES or set(ordered) != {
        str(index) for index in range(1, NUM_CLASSES + 1)
    }:
        raise ValueError("Dataset must contain the Oxford Flowers category directories 1 through 102")
    return ordered


def save_artifact(
    path: str | Path,
    model: nn.Module,
    class_to_idx: dict[str, int],
    labels: dict[str, str],
    metrics: dict[str, float],
) -> None:
    categories = category_order(class_to_idx)
    artifact = {
        "schema_version": 1,
        "architecture": ARCHITECTURE,
        "num_classes": NUM_CLASSES,
        "input_size": INPUT_SIZE,
        "normalization": {"mean": IMAGENET_MEAN, "std": IMAGENET_STD},
        "state_dict": {key: value.detach().cpu() for key, value in model.state_dict().items()},
        "categories": categories,
        "class_names": [labels[category] for category in categories],
        "metrics": metrics,
    }
    target = Path(path)
    target.parent.mkdir(parents=True, exist_ok=True)
    torch.save(artifact, target)


def load_artifact(path: str | Path, device: torch.device) -> tuple[nn.Module, dict]:
    artifact = torch.load(path, map_location=device, weights_only=True)
    if artifact.get("schema_version") != 1:
        raise ValueError("Unsupported BloomAI model artifact schema")
    if artifact.get("architecture") != ARCHITECTURE:
        raise ValueError("Artifact architecture is not MobileNetV3-Small")
    if artifact.get("num_classes") != NUM_CLASSES:
        raise ValueError("Artifact must contain exactly 102 classes")
    model = build_model(NUM_CLASSES, pretrained=False)
    model.load_state_dict(artifact["state_dict"], strict=True)
    model.to(device).eval()
    return model, artifact
