"""Checksum-gated MobileNetV3 inference runtime."""

from __future__ import annotations

import hashlib
import os
import threading
from pathlib import Path

import gdown
import torch
from PIL import Image
from torch import nn
from torchvision import models, transforms

EXPECTED_SHA256 = "9ee2f29556562a14a666ad8345b850b7aa11d26dc2e73b16a735d4d33b515dc9"
NUM_CLASSES = 102


class ModelRuntime:
    def __init__(self) -> None:
        self.path = Path(os.getenv("MODEL_PATH", "/app/models/mobilenet_v3_small_flowers102.pth"))
        self.expected_sha256 = os.getenv("MODEL_SHA256", EXPECTED_SHA256).lower()
        self.file_id = os.getenv("MODEL_GDRIVE_FILE_ID", "").strip()
        self.model: nn.Module | None = None
        self.metadata: dict = {}
        self.error: str | None = None
        self._lock = threading.Lock()
        self._transform = transforms.Compose([
            transforms.Resize(256), transforms.CenterCrop(224), transforms.ToTensor(),
            transforms.Normalize([0.485, 0.456, 0.406], [0.229, 0.224, 0.225]),
        ])

    @staticmethod
    def sha256(path: Path) -> str:
        digest = hashlib.sha256()
        with path.open("rb") as handle:
            for block in iter(lambda: handle.read(1024 * 1024), b""):
                digest.update(block)
        return digest.hexdigest()

    def _provision(self) -> None:
        self.path.parent.mkdir(parents=True, exist_ok=True)
        if self.path.is_file() and self.sha256(self.path) == self.expected_sha256:
            return
        if not self.file_id:
            raise RuntimeError("MODEL_GDRIVE_FILE_ID is required when the model is absent")
        temporary = self.path.with_suffix(self.path.suffix + ".download")
        temporary.unlink(missing_ok=True)
        result = gdown.download(id=self.file_id, output=str(temporary), quiet=True)
        if not result or not temporary.is_file():
            raise RuntimeError("Model download failed")
        actual = self.sha256(temporary)
        if actual != self.expected_sha256:
            temporary.unlink(missing_ok=True)
            raise RuntimeError(f"Model checksum mismatch: expected {self.expected_sha256}, got {actual}")
        temporary.replace(self.path)

    def initialize(self) -> None:
        try:
            self._provision()
            artifact = torch.load(self.path, map_location="cpu", weights_only=True)
            if artifact.get("schema_version") != 1:
                raise ValueError("Unsupported model artifact schema")
            if artifact.get("architecture") != "mobilenet_v3_small":
                raise ValueError("Unsupported model architecture")
            if artifact.get("num_classes") != NUM_CLASSES:
                raise ValueError("Model artifact must contain exactly 102 classes")
            if len(artifact.get("categories", [])) != NUM_CLASSES:
                raise ValueError("Model artifact category metadata is incomplete")
            if len(artifact.get("class_names", [])) != NUM_CLASSES:
                raise ValueError("Model artifact class-name metadata is incomplete")
            model = models.mobilenet_v3_small(weights=None)
            model.classifier[-1] = nn.Linear(model.classifier[-1].in_features, NUM_CLASSES)
            model.load_state_dict(artifact["state_dict"], strict=True)
            model.eval()
            self.model = model
            self.metadata = artifact
            self.error = None
        except Exception as exc:
            self.model = None
            self.metadata = {}
            self.error = str(exc)

    @property
    def ready(self) -> bool:
        return self.model is not None and self.error is None

    def status(self) -> dict:
        if not self.ready:
            return {"status": "not_ready", "model_loaded": False, "error": self.error}
        return {
            "status": "ready", "model_loaded": True,
            "architecture": self.metadata["architecture"],
            "classes": self.metadata["num_classes"], "sha256": self.expected_sha256,
            "metrics": self.metadata.get("metrics", {}),
        }

    def predict(self, image: Image.Image, top_k: int = 5) -> list[dict]:
        if not self.ready or self.model is None:
            raise RuntimeError("Model is not ready")
        inputs = self._transform(image.convert("RGB")).unsqueeze(0)
        with self._lock, torch.inference_mode():
            probabilities = torch.softmax(self.model(inputs), dim=1)
            scores, indices = probabilities.topk(top_k, dim=1)
        categories = self.metadata["categories"]
        names = self.metadata["class_names"]
        return [
            {"class_index": index, "category_id": categories[index], "name": names[index], "confidence": score}
            for score, index in zip(scores[0].tolist(), indices[0].tolist())
        ]


runtime = ModelRuntime()
