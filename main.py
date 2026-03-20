"""
FastAPI Cloud Server for Sign Language Recognition
Uses YOLOv8 (Ultralytics) for real-time inference on hand gesture images.
"""

import io
import logging
import time
from contextlib import asynccontextmanager

import numpy as np
from fastapi import FastAPI, File, HTTPException, UploadFile
from fastapi.middleware.cors import CORSMiddleware
from PIL import Image

# ---------------------------------------------------------------------------
# Logging
# ---------------------------------------------------------------------------
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s | %(levelname)-8s | %(message)s",
)
logger = logging.getLogger("sign-language-server")

# ---------------------------------------------------------------------------
# Global model reference
# ---------------------------------------------------------------------------
model = None


def load_model():
    """Load the YOLOv8 model once at startup."""
    global model
    try:
        from ultralytics import YOLO

        model = YOLO("best.pt")
        logger.info("YOLOv8 model loaded successfully from best.pt")
    except FileNotFoundError:
        logger.error("best.pt not found – place your trained model in the server/ dir")
        raise
    except Exception as exc:
        logger.error("Failed to load YOLOv8 model: %s", exc)
        raise


# ---------------------------------------------------------------------------
# Application lifespan (startup / shutdown)
# ---------------------------------------------------------------------------
@asynccontextmanager
async def lifespan(app: FastAPI):
    load_model()
    yield
    logger.info("Server shutting down")


# ---------------------------------------------------------------------------
# FastAPI app
# ---------------------------------------------------------------------------
app = FastAPI(
    title="Sign Language Recognition API",
    description="Accepts hand-gesture images and returns predicted sign letters using YOLOv8.",
    version="1.0.0",
    lifespan=lifespan,
)

# CORS – allow all origins so ESP32 and any test client can reach it
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# ---------------------------------------------------------------------------
# Routes
# ---------------------------------------------------------------------------
@app.get("/health")
async def health():
    """Return server & model status."""
    return {
        "status": "ok",
        "model_loaded": model is not None,
    }


@app.post("/predict")
async def predict(file: UploadFile = File(...)):
    """
    Accept an image (multipart/form-data), run YOLOv8 inference,
    and return the top prediction with confidence.
    """
    if model is None:
        raise HTTPException(status_code=503, detail="Model not loaded")

    # --- validate content type -------------------------------------------
    if file.content_type and not file.content_type.startswith("image/"):
        raise HTTPException(
            status_code=400,
            detail=f"Expected an image file, got {file.content_type}",
        )

    try:
        # --- read & decode image -----------------------------------------
        contents = await file.read()
        image = Image.open(io.BytesIO(contents)).convert("RGB")
        logger.info(
            "Received image: %s  size=%s  bytes=%d",
            file.filename,
            image.size,
            len(contents),
        )

        # --- inference ----------------------------------------------------
        start = time.time()
        results = model(np.array(image), verbose=False)
        elapsed = time.time() - start
        logger.info("Inference completed in %.3f s", elapsed)

        # --- extract best prediction ------------------------------------
        result = results[0]

        if result.boxes is not None and len(result.boxes):
            # Find the detection with highest confidence
            confidences = result.boxes.conf.cpu().numpy()
            class_ids = result.boxes.cls.cpu().numpy().astype(int)
            best_idx = int(np.argmax(confidences))
            best_conf = float(confidences[best_idx])
            best_cls = class_ids[best_idx]

            # Map class index to name (from model metadata)
            prediction = result.names.get(best_cls, str(best_cls))

            return {
                "prediction": prediction,
                "confidence": round(best_conf, 4),
                "inference_time_ms": round(elapsed * 1000, 1),
            }

        # No detections
        return {
            "prediction": "No sign detected",
            "confidence": 0.0,
            "inference_time_ms": round(elapsed * 1000, 1),
        }

    except HTTPException:
        raise
    except Exception as exc:
        logger.exception("Prediction failed")
        raise HTTPException(status_code=500, detail=f"Prediction error: {exc}")


# ---------------------------------------------------------------------------
# Standalone entry-point (for local dev)
# ---------------------------------------------------------------------------
if __name__ == "__main__":
    import uvicorn

    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)
