"""Download and validate the Oxford Flowers 102 dataset."""

from __future__ import annotations

import argparse
import shutil
import tarfile
from pathlib import Path

import gdown

DATASET_FILE_ID = "1Ph_upVnd325zxt8IpZlnaB8lLzrsdP9s"


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Prepare the BloomAI training dataset")
    parser.add_argument("--data-dir", type=Path, default=Path("data"))
    return parser.parse_args()


def validate(dataset_dir: Path) -> None:
    for split in ("train", "valid", "test"):
        split_dir = dataset_dir / split
        if not split_dir.is_dir():
            raise RuntimeError(f"Dataset is missing split: {split_dir}")
        categories = {path.name for path in split_dir.iterdir() if path.is_dir()}
        if categories != {str(index) for index in range(1, 103)}:
            raise RuntimeError(f"{split} must contain category directories 1 through 102")


def normalize_layout(data_dir: Path, dataset_dir: Path) -> None:
    """Find a valid extracted root and normalize it to data/flowers."""
    candidates = sorted(
        {path.parent for path in data_dir.rglob("train") if path.is_dir()},
        key=lambda path: (len(path.parts), str(path)),
    )
    source = None
    for candidate in candidates:
        try:
            validate(candidate)
        except RuntimeError:
            continue
        source = candidate
        break
    if source is None:
        raise RuntimeError("Archive did not contain valid train, valid, and test splits")
    if source.resolve() == dataset_dir.resolve():
        return
    dataset_dir.mkdir(parents=True, exist_ok=True)
    for split in ("train", "valid", "test"):
        target = dataset_dir / split
        if target.exists():
            shutil.rmtree(target)
        shutil.move(str(source / split), str(target))
    validate(dataset_dir)


def main() -> None:
    args = parse_args()
    archive = args.data_dir / "flower_data.tar.gz"
    dataset_dir = args.data_dir / "flowers"
    args.data_dir.mkdir(parents=True, exist_ok=True)
    try:
        validate(dataset_dir)
        print(f"Validated existing dataset at {dataset_dir}")
        return
    except RuntimeError:
        pass
    if not archive.is_file():
        gdown.download(id=DATASET_FILE_ID, output=str(archive), quiet=False)
    if not archive.is_file():
        raise RuntimeError("Dataset download did not produce an archive")
    with tarfile.open(archive, mode="r:gz") as bundle:
        bundle.extractall(args.data_dir, filter="data")
    normalize_layout(args.data_dir, dataset_dir)
    validate(dataset_dir)
    print(f"Dataset ready at {dataset_dir}")


if __name__ == "__main__":
    main()
