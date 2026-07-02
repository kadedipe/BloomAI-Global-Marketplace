import tarfile
from pathlib import Path

import gdown
from config import FLOWER_DATA, CHECKPOINT, MODEL_STATE

FILES = {
    "flower_data": {
        "id": "1Ph_upVnd325zxt8IpZlnaB8lLzrsdP9s",
        "output": FLOWER_DATA,
    },
    "checkpoint": {
        "id": "1qQJTdCYL9Dw2iM7conia_hh9YihYNpzI",
        "output": CHECKPOINT,
    },
    "model_state_dict": {
        "id": "1UhPBAyWdSEWgvrNtM2RQLQrJ-j0nxZ6B",
        "output": MODEL_STATE,
    },
}


def download_file(file_id, output_path):
    output_path = Path(output_path)

    if output_path.exists():
        print(f"{output_path.name} already exists.")
        return

    url = f"https://drive.google.com/uc?id={file_id}"
    print(f"Downloading {output_path.name}...")
    gdown.download(url, str(output_path), quiet=False)


def download_all():
    for item in FILES.values():
        download_file(item["id"], item["output"])


def extract_dataset():
    if not FLOWER_DATA.exists():
        return

    extract_folder = FLOWER_DATA.parent / "flowers"

    if extract_folder.exists():
        print("Dataset already extracted.")
        return

    print("Extracting dataset...")

    with tarfile.open(FLOWER_DATA) as tar:
        tar.extractall(FLOWER_DATA.parent)

    print("Done()")