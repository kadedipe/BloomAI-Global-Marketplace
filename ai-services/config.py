from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent

MODEL_DIR = BASE_DIR / "models"
DATA_DIR = BASE_DIR / "data"

MODEL_DIR.mkdir(exist_ok=True)
DATA_DIR.mkdir(exist_ok=True)

DATASET_DIR = DATA_DIR / "flowers"
DATASET_DIR.mkdir(exist_ok=True)

FLOWER_DATA = DATA_DIR / "flower_data.tar.gz"
CHECKPOINT = MODEL_DIR / "checkpoint.pth"
MODEL_STATE = MODEL_DIR / "model_state_dict.pth"