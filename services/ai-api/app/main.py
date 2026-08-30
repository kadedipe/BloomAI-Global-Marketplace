import io
import os
from contextlib import asynccontextmanager

import sentry_sdk
from fastapi import FastAPI, File, HTTPException, UploadFile
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from PIL import Image, UnidentifiedImageError

from app.model_runtime import runtime

origins = [item.strip().rstrip("/") for item in os.getenv("CORS_ORIGINS", "http://localhost:5173").split(",")]
if os.getenv("SENTRY_DSN"):
    sentry_sdk.init(
        dsn=os.environ["SENTRY_DSN"],
        environment=os.getenv("ENVIRONMENT", "development"),
        release=os.getenv("RAILWAY_GIT_COMMIT_SHA"),
        traces_sample_rate=float(os.getenv("SENTRY_TRACES_SAMPLE_RATE", "0.1")),
        send_default_pii=False,
    )


@asynccontextmanager
async def lifespan(_: FastAPI):
    runtime.initialize()
    yield


app = FastAPI(title="BloomAI Inference API", version="2.0.0", lifespan=lifespan)
app.add_middleware(CORSMiddleware, allow_origins=origins, allow_methods=["GET", "POST"], allow_headers=["Content-Type"])


@app.get("/health/live")
async def live():
    return {"status": "ok", "service": "ai-api"}


@app.get("/health/ready")
async def ready():
    status = runtime.status()
    return status if runtime.ready else JSONResponse(status_code=503, content=status)


@app.post("/api/v1/classify")
async def classify(image: UploadFile = File(...)):
    if image.content_type not in {"image/jpeg", "image/png", "image/webp"}:
        raise HTTPException(415, "Upload a JPEG, PNG, or WebP image")
    data = await image.read(10 * 1024 * 1024 + 1)
    if len(data) > 10 * 1024 * 1024:
        raise HTTPException(413, "Image exceeds the 10 MB limit")
    try:
        parsed = Image.open(io.BytesIO(data))
        parsed.verify()
    except (UnidentifiedImageError, OSError) as exc:
        raise HTTPException(422, "The uploaded file is not a valid image") from exc
    if not runtime.ready:
        raise HTTPException(503, "The flower model is not ready")
    parsed = Image.open(io.BytesIO(data)).convert("RGB")
    try:
        predictions = runtime.predict(parsed, top_k=5)
    except RuntimeError as exc:
        raise HTTPException(503, str(exc)) from exc
    return {"model": "mobilenet_v3_small", "model_sha256": runtime.expected_sha256, "predictions": predictions}
