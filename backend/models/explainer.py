import logging
from typing import Any, Dict, List, Optional, Tuple

import numpy as np
import pandas as pd

from utils.config import MODE_BENCHMARKS, MODEL_FEATURES

logger = logging.getLogger(__name__)

FEATURE_META = {
    "Accuracy": {"label": "Accuracy", "unit": "%"},
    "Headshot_Ratio": {"label": "Headshot Rate", "unit": "%"},
    "KD_Ratio": {"label": "K/D Ratio", "unit": ""},
    "Avg_Kills_Per_Match": {"label": "Avg Kills / Match", "unit": ""},
    "Avg_Damage_Per_Match": {"label": "Avg Damage / Match", "unit": ""},
    "Win_Ratio": {"label": "Win Rate", "unit": "%"},
    "Top10_Ratio": {"label": "Top 10 Rate", "unit": "%"},
}


def _unwrap_estimator(model) -> Tuple[Any, List[Tuple[str, Any]]]:
    """Find the actual fitted tree/linear estimator inside common wrapper
    types (sklearn Pipeline, GridSearchCV/RandomizedSearchCV), so SHAP's
    TreeExplainer and the feature_importances_/coef_ fallback don't
    silently fail just because they were handed the wrapper object instead
    of the model itself.

    Returns (estimator, preprocessing_steps), where preprocessing_steps is
    the ordered list of (name, transformer) pairs — everything in the
    Pipeline BEFORE the final estimator — that must be applied to a raw
    feature row before it's in the space the estimator actually expects.
    """
    if hasattr(model, "best_estimator_"):  # GridSearchCV / RandomizedSearchCV
        return _unwrap_estimator(model.best_estimator_)
    if hasattr(model, "steps"):  # sklearn Pipeline
        steps = model.steps
        return steps[-1][1], list(steps[:-1])
    return model, []


def _apply_preprocessing(steps: List[Tuple[str, Any]], x: np.ndarray) -> np.ndarray:
    for _, transformer in steps:
        x = transformer.transform(x)
    return x


class ModelExplainer:
    def __init__(self):
        self.explainer = None
        self.feature_names = MODEL_FEATURES
        self.estimator = None
        self.preprocessing_steps: List[Tuple[str, Any]] = []

    def load(self, model, feature_names: List[str]):
        self.feature_names = feature_names
        self.estimator, self.preprocessing_steps = _unwrap_estimator(model)
        try:
            import shap
            self.explainer = shap.TreeExplainer(self.estimator)
        except Exception as exc:
            logger.warning(
                "Could not build SHAP TreeExplainer for %r: %s — "
                "per-player explanations will use the feature_importances_/"
                "coef_ fallback instead.",
                type(self.estimator), exc,
            )
            self.explainer = None

    def _shap_values(self, x: np.ndarray) -> Optional[np.ndarray]:
        if self.explainer is None:
            return None
        try:
            x_transformed = _apply_preprocessing(self.preprocessing_steps, x)
            values = self.explainer.shap_values(x_transformed)
            if isinstance(values, list):
                values = values[1] if len(values) > 1 else values[0]
            values = np.asarray(values)
            if values.ndim == 3:
                values = values[:, :, 1]
            return values[0]
        except Exception as exc:
            logger.warning("SHAP shap_values() failed: %s", exc)
            return None

    def _fallback_importance(self) -> np.ndarray:
        estimator = self.estimator
        importance = getattr(estimator, "feature_importances_", None)
        if importance is None and hasattr(estimator, "coef_"):
            coef = np.asarray(estimator.coef_)
            importance = np.abs(coef[0] if coef.ndim > 1 else coef)
        if importance is None:
            logger.warning(
                "No feature_importances_ or coef_ found on %r — "
                "contribution values will be 0 until this model type is "
                "supported by the fallback path.",
                type(estimator),
            )
            return np.zeros(len(self.feature_names))
        return np.asarray(importance, dtype=float)

    def explain(self, model, x_row: np.ndarray, stats: Dict[str, Any], mode: Optional[str]) -> List[Dict[str, Any]]:
        # `model` is accepted for backward-compatible call signatures, but
        # self.estimator (set in load(), already unwrapped from any
        # Pipeline) is what's actually used for both SHAP and the
        # fallback, since that's the object SHAP/feature_importances_ can
        # work with.
        shap_values = self._shap_values(x_row)
        if shap_values is None:
            shap_values = self._fallback_importance()

        pairs = sorted(
            zip(self.feature_names, shap_values),
            key=lambda x: abs(float(x[1])),
            reverse=True,
        )[:8]

        evidence = []
        for feature, contribution in pairs:
            if feature == "Mode_Code" or feature not in stats:
                continue
            value_obj = stats.get(feature, {})
            value = value_obj.get("value") if isinstance(value_obj, dict) else value_obj
            if value is None:
                continue

            legit_range = None
            if feature == "Accuracy" and mode in MODE_BENCHMARKS:
                legit_range = f"{MODE_BENCHMARKS[mode]['accuracy'][0]}–{MODE_BENCHMARKS[mode]['accuracy'][1]}%"
            elif feature == "Headshot_Ratio" and mode in MODE_BENCHMARKS:
                legit_range = f"{MODE_BENCHMARKS[mode]['headshot'][0]}–{MODE_BENCHMARKS[mode]['headshot'][1]}%"

            indicator = "normal"
            if legit_range:
                bounds = MODE_BENCHMARKS[mode]["accuracy" if feature == "Accuracy" else "headshot"]
                if float(value) > bounds[1] * 1.5:
                    indicator = "highly_unusual"
                elif float(value) > bounds[1]:
                    indicator = "suspicious"
                elif float(value) > bounds[1] * 1.15:
                    indicator = "unusual"

            label = FEATURE_META.get(feature, {"label": feature, "unit": ""})["label"]
            direction = "increased" if float(contribution) > 0 else "decreased"
            explanation = (
                f"{label} contributed {direction} suspicion in the model's decision."
            )

            evidence.append({
                "feature": label,
                "player_value": float(value),
                "legit_range": legit_range,
                "indicator": indicator,
                "contribution": float(contribution),
                "explanation": explanation,
            })
        return evidence