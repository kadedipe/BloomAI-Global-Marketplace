import io
import os
from pathlib import Path
from fastapi import FastAPI, File, HTTPException, UploadFile
from fastapi.middleware.cors import CORSMiddleware
from PIL import Image, UnidentifiedImageError

MODEL_PATH = Path(os.getenv("MODEL_PATH", "/app/models/checkpoint.pth"))
origins = [item.strip().rstrip("/") for item in os.getenv("CORS_ORIGINS", "http://localhost:5173").split(",")]
app = FastAPI(title="BloomAI Inference API", version="1.0.0")
app.add_middleware(CORSMiddleware, allow_origins=origins, allow_methods=["GET", "POST"], allow_headers=["Content-Type"])

@app.get("/health/live")
async def live(): return {"status":"ok", "service":"ai-api"}

@app.get("/health/ready")
async def ready():
    return {"status":"ready" if MODEL_PATH.is_file() else "model_required", "model_loaded":MODEL_PATH.is_file()}

@app.post("/api/v1/classify")
async def classify(image: UploadFile = File(...)):
    if image.content_type not in {"image/jpeg", "image/png", "image/webp"}:
        raise HTTPException(415, "Upload a JPEG, PNG, or WebP image")
    data = await image.read(10 * 1024 * 1024 + 1)
    if len(data) > 10 * 1024 * 1024: raise HTTPException(413, "Image exceeds the 10 MB limit")
    try:
        parsed = Image.open(io.BytesIO(data)); parsed.verify()
    except (UnidentifiedImageError, OSError): raise HTTPException(422, "The uploaded file is not a valid image")
    if not MODEL_PATH.is_file():
        raise HTTPException(503, "The flower model has not been provisioned. Set MODEL_PATH to a trained checkpoint.")
    raise HTTPException(501, "Model adapter not configured for this checkpoint format")

