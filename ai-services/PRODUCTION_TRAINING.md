# Production flower model

BloomAI's production classifier uses MobileNetV3-Small with exactly 102 outputs. The legacy VGG16 checkpoint is not used because it contains a 1,000-output head and incorrect class metadata.

## Train

Run from `ai-services` after extracting the Oxford Flowers dataset into `data/flowers/{train,valid,test}`:

```bash
python -m pip install -r requirements-production.txt
python prepare_dataset.py
python train_production.py data/flowers --labels data/flower_labels.json
```

For Google Colab, select a GPU runtime and keep the generated files under `models/` in mounted Drive storage. The trainer freezes the pretrained backbone for three epochs, fine-tunes the whole network, applies early stopping, evaluates the untouched test split once, and exports an inference-only artifact.

## Release gates

- `num_classes` is exactly 102.
- Train, validation, and test mappings are identical.
- The test split is not used for model selection.
- `models/metrics.json` is retained with the release evidence.
- The artifact checksum is recorded before deployment.
- A release must not claim accuracy that is absent from `models/metrics.json`.

Generate a checksum:

```bash
sha256sum models/mobilenet_v3_small_flowers102.pth
```

Upload the artifact to production object storage, then configure the AI API with its download location and checksum. Never commit model binaries to Git.


## Google Colab GPU

Do not install `requirements-production.txt` in a GPU-enabled Colab runtime because that file intentionally pins CPU-only wheels for CI and deployment. Colab already supplies a CUDA-enabled PyTorch build.

After copying and extracting the repository ZIP to `/content`, run:

```bash
python -m pip install -r requirements-colab.txt
python prepare_dataset.py
python train_production.py data/flowers --labels data/flower_labels.json \
  --output /content/drive/MyDrive/BloomAI-Colab/artifacts/mobilenet_v3_small_flowers102.pth \
  --metrics-output /content/drive/MyDrive/BloomAI-Colab/artifacts/metrics.json
```

Train from Colab's local `/content` disk and write only release artifacts to mounted Drive. This avoids slow per-image reads through the Drive mount.
