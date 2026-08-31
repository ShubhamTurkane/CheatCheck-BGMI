from typing import Any, Dict

from ocr.extractor import extract_stats
from models.predictor import ModelPredictor
from models.explainer import ModelExplainer
from utils.config import DISCLAIMER_TEXT

MIN_REQUIRED_STATS = 4
MIN_CONFIDENCE = 0.5


class Analyzer:
    def __init__(self, predictor: ModelPredictor, explainer: ModelExplainer):
        self.predictor = predictor
        self.explainer = explainer

    def run(self, image_path: str, original_filename: str = "") -> Dict[str, Any]:
        if not self.predictor.is_loaded:
            raise RuntimeError("Model is not loaded. Please train it first.")

        ocr_result = extract_stats(image_path)
        mode = ocr_result["mode"]
        stats = ocr_result["stats"]
        warnings = ocr_result["warnings"]

        confident_stats = {
            name: obj for name, obj in stats.items()
            if obj.get("confidence", 0) >= MIN_CONFIDENCE
        }

        extracted = {
            "mode": mode,
            "stats": [
                {
                    "name": name,
                    "value": obj.get("value"),
                    "raw": obj.get("raw"),
                    "confidence": obj.get("confidence", 0),
                    "source": obj.get("source", "ocr"),
                }
                for name, obj in stats.items()
            ],
            "warnings": warnings,
        }

        # --- Validation gate: refuse to predict on insufficient/invalid data ---
        if not ocr_result.get("is_valid_screenshot") or len(confident_stats) < MIN_REQUIRED_STATS:
            return {
                "verdict": "insufficient_data",
                "suspicion_score": 0.0,
                "risk_level": "unknown",
                "risk_color": "gray",
                "model_confidence": 0.0,
                "prediction_label": "insufficient_data",
                "probability": 0.0,
                "message": (
                    f"This doesn't look like a valid BGMI stats screenshot "
                    f"(only {len(confident_stats)} field(s) confidently detected). "
                    f"Please upload a clear stats screenshot."
                ),
                "extracted_stats": extracted,
                "evidence": [],
                "feature_importance": [],
                "disclaimer": DISCLAIMER_TEXT,
                "model_info": self.predictor.get_model_info(),
            }
        # -------------------------------------------------------------------

        prediction = self.predictor.predict(stats, mode)
        x_row = self.predictor._build_feature_vector(stats, mode)
        evidence = self.explainer.explain(
            self.predictor.model, x_row, stats, mode
        )

        return {
            "verdict": "prediction",
            **prediction,
            "extracted_stats": extracted,
            "evidence": evidence,
            "feature_importance": self.predictor.feature_importance,
            "disclaimer": DISCLAIMER_TEXT,
            "model_info": self.predictor.get_model_info(),
        }