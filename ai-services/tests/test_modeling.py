import json

import torch

from modeling import NUM_CLASSES, build_model, category_order, load_artifact, load_labels, save_artifact


def test_model_has_exactly_102_outputs():
    model = build_model(pretrained=False)
    assert model.classifier[-1].out_features == NUM_CLASSES


def test_category_order_matches_imagefolder_lexical_order():
    categories = sorted(str(index) for index in range(1, NUM_CLASSES + 1))
    mapping = {category: index for index, category in enumerate(categories)}
    assert category_order(mapping) == categories


def test_artifact_round_trip(tmp_path):
    model = build_model(pretrained=False)
    categories = sorted(str(index) for index in range(1, NUM_CLASSES + 1))
    mapping = {category: index for index, category in enumerate(categories)}
    labels = {str(index): f"flower-{index}" for index in range(1, NUM_CLASSES + 1)}
    label_path = tmp_path / "labels.json"
    label_path.write_text(json.dumps(labels), encoding="utf-8")
    artifact_path = tmp_path / "model.pth"
    save_artifact(artifact_path, model, mapping, load_labels(label_path), {"test_accuracy": 0.75})
    loaded, metadata = load_artifact(artifact_path, torch.device("cpu"))
    assert loaded.classifier[-1].out_features == NUM_CLASSES
    assert metadata["categories"] == categories
    assert metadata["metrics"]["test_accuracy"] == 0.75
