import json
import logging
from typing import Any, Dict, List, Optional

import joblib
import numpy as np
import pandas as pd

from utils.config import MODEL_DIR, MODEL_FEATURES, RISK_COLORS, RISK_THRESHOLDS

logger = logging.getLogger(__name__)

class ModelPredictor:
    def __init__(self):
        self.model = None
        self.scaler = None
        self.feature_names: List[str] = MODEL_FEATURES
        self.metrics: Dict[str, Any] = {}
        self.feature_importance: List[Dict[str, Any]] = []
        self.confusion_matrix: Optional[List[List[int]]] = None
        self.dataset_summary: Dict[str, Any] = {}
        self.model_name: Optional[str] = None
        self.is_loaded = False
        self.is_experimental = True

    def load(self) -> bool:
        model_path = MODEL_DIR / "model.pkl"
        if not model_path.exists():
            logger.warning("No trained model found at %s", model_path)
            return False
        try:
            self.model = joblib.load(model_path)
            scaler_path = MODEL_DIR / "scaler.pkl"
            self.scaler = joblib.load(scaler_path) if scaler_path.exists() else None
            for name, default in [
                ("metrics.json", {}),
                ("feature_importance.json", []),
                ("dataset_summary.json", {}),
            ]:
                path = MODEL_DIR / name
                if not path.exists():
                    continue
                data = json.loads(path.read_text(encoding="utf-8"))
                if name == "metrics.json":
                    self.metrics = data
                    self.model_name = data.get("model_name", "unknown")
                    self.confusion_matrix = data.get("confusion_matrix")
                    self.is_experimental = data.get("is_experimental", True)
                elif name == "feature_importance.json":
                    self.feature_importance = data
                else:
                    self.dataset_summary = data
            self.is_loaded = True
            return True
        except Exception as exc:
            logger.exception("Failed to load model: %s", exc)
            return False

    def _build_feature_vector(self, stats: Dict[str, Any], mode: Optional[str]) -> np.ndarray:
        mode_code = {"Solo": 0, "Duo": 1, "Squad": 2}.get(mode or "", -1)
        row = {}
        for feature in MODEL_FEATURES:
            if feature == "Mode_Code":
                row[feature] = mode_code
                continue
            obj = stats.get(feature)
            value = obj.get("value") if isinstance(obj, dict) else obj
            row[feature] = float(value) if value is not None else 0.0

        frame = pd.DataFrame([row], columns=MODEL_FEATURES)
        if self.scaler is not None:
            frame = pd.DataFrame(
                self.scaler.transform(frame),
                columns=MODEL_FEATURES
            )
        return frame.to_numpy(dtype=float)

    def predict(self, stats: Dict[str, Any], mode: Optional[str]) -> Dict[str, Any]:
        if not self.is_loaded:
            raise RuntimeError("Model is not loaded. Run the training command first.")

        x = self._build_feature_vector(stats, mode)
        probability = float(self.model.predict_proba(x)[0, 1])
        score = round(probability * 100, 1)
        risk_level = self._risk_level(score)
        return {
            "probability": round(probability, 4),
            "prediction_label": "Suspicious" if probability >= 0.5 else "Legit",
            "suspicion_score": score,
            "risk_level": risk_level,
            "risk_color": RISK_COLORS[risk_level],
            "model_confidence": round(max(probability, 1 - probability), 3),
        }

    @staticmethod
    def _risk_level(score: float) -> str:
        for level, (lo, hi) in RISK_THRESHOLDS.items():
            if lo <= score <= hi:
                return level
        return "extremely_suspicious" if score > 80 else "likely_legit"

    def get_model_info(self) -> Dict[str, Any]:
        return {
            "model_name": self.model_name or "unknown",
            "metrics": self.metrics,
            "feature_importance": self.feature_importance,
            "confusion_matrix": self.confusion_matrix or [[0, 0], [0, 0]],
            "dataset_summary": self.dataset_summary,
            "is_experimental": self.is_experimental,
        }
