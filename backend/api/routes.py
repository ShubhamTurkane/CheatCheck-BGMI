import uuid
from pathlib import Path

from fastapi import APIRouter, File, HTTPException, Request, UploadFile

from api.schemas import HealthResponse, AnalysisResult, ModelInfoResponse
from services.analyzer import Analyzer
from utils.config import MAX_UPLOAD_MB, TEMP_DIR, DISCLAIMER_TEXT

router = APIRouter()
ALLOWED_EXT = {".png", ".jpg", ".jpeg", ".webp"}

@router.get("/health", response_model=HealthResponse)
def health(request: Request):
    predictor = request.app.state.predictor
    return HealthResponse(
        status="ok",
        model_loaded=predictor.is_loaded,
        model_name=predictor.model_name,
        feature_count=len(predictor.feature_names) if predictor.is_loaded else None,
    )

@router.post("/analyze", response_model=AnalysisResult)
async def analyze(request: Request, file: UploadFile = File(...)):
    ext = Path(file.filename or "").suffix.lower()
    if ext not in ALLOWED_EXT:
        raise HTTPException(400, f"Unsupported file type '{ext}'. Use PNG/JPG/JPEG/WEBP.")

    contents = await file.read()
    if not contents:
        raise HTTPException(400, "Empty file.")
    if len(contents) > MAX_UPLOAD_MB * 1024 * 1024:
        raise HTTPException(413, f"File too large. Max {MAX_UPLOAD_MB}MB.")

    # Verify the image header through Pillow/OpenCV in the OCR layer.
    tmp_path = TEMP_DIR / f"{uuid.uuid4().hex}{ext}"
    try:
        tmp_path.write_bytes(contents)
        analyzer = Analyzer(
            predictor=request.app.state.predictor,
            explainer=request.app.state.explainer,
        )
        return analyzer.run(str(tmp_path), original_filename=file.filename or "")
    except ValueError as exc:
        raise HTTPException(422, str(exc)) from exc
    except RuntimeError as exc:
        raise HTTPException(503, str(exc)) from exc
    except Exception as exc:
        raise HTTPException(500, f"Analysis failed: {exc}") from exc
    finally:
        try:
            tmp_path.unlink(missing_ok=True)
        except OSError:
            pass

@router.get("/model/info", response_model=ModelInfoResponse)
def model_info(request: Request):
    predictor = request.app.state.predictor
    if not predictor.is_loaded:
        raise HTTPException(
            503,
            "Model not loaded. Run `python -m ml.training.train` first."
        )
    return ModelInfoResponse(**predictor.get_model_info())
