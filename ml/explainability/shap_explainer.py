import logging

import numpy as np

logger = logging.getLogger(__name__)


def _unwrap_estimator(model):
    """Return the underlying fitted estimator that actually exposes
    feature_importances_ / coef_, even when `model` is wrapped in a
    scikit-learn Pipeline, GridSearchCV/RandomizedSearchCV, or similar.

    Without this, hasattr(model, "feature_importances_") is False for a
    Pipeline even though its final step has real importances — which is
    almost certainly why every contribution value has been coming back as
    exactly 0 regardless of the player's stats: the code was silently
    falling through to np.zeros(...) every single time.
    """
    seen = set()
    candidate = model
    while candidate is not None and id(candidate) not in seen:
        seen.add(id(candidate))
        if hasattr(candidate, "feature_importances_") or hasattr(candidate, "coef_"):
            return candidate
        if hasattr(candidate, "steps"):  # sklearn Pipeline
            candidate = candidate.steps[-1][1]
            continue
        if hasattr(candidate, "best_estimator_"):  # GridSearchCV / RandomizedSearchCV
            candidate = candidate.best_estimator_
            continue
        break
    return candidate


def _fallback_importances(model, feature_names) -> np.ndarray:
    """Used only when SHAP itself is unavailable or raises. Tries to find a
    real fitted estimator inside common wrapper types first, so a
    Pipeline-wrapped model doesn't automatically mean 'no signal'. Only
    returns all-zeros as an absolute last resort, and logs clearly when
    that happens so it's visible in server logs rather than silently
    reaching the frontend as an unexplained 0.
    """
    estimator = _unwrap_estimator(model)
    if estimator is not None and hasattr(estimator, "feature_importances_"):
        return np.asarray(estimator.feature_importances_, dtype=float)
    if estimator is not None and hasattr(estimator, "coef_"):
        coef = np.asarray(estimator.coef_, dtype=float)
        return np.abs(coef[0] if coef.ndim > 1 else coef)

    logger.warning(
        "No feature_importances_ or coef_ found on model %r (or on any "
        "wrapped estimator inside it) — falling back to zeros. This model "
        "type isn't supported by the fallback path yet; contribution "
        "values will read as 0 until that's added.",
        type(model),
    )
    return np.zeros(len(feature_names))


def compute_feature_importance(model, feature_names, X_background) -> list:
    """Global feature importance, averaged across a background dataset.

    Useful for a model-wide 'what matters most in general' view — but NOT
    a per-player explanation, since every player gets the exact same
    numbers back regardless of their own stats. Kept for backward
    compatibility with any existing callers. For the per-analysis "Model
    contribution" chart on a specific player's result page, use
    compute_player_contributions() below instead.
    """
    try:
        import shap
        explainer = shap.TreeExplainer(model)
        values = explainer.shap_values(X_background)
        if isinstance(values, list):
            values = values[1] if len(values) > 1 else values[0]
        values = np.asarray(values)
        if values.ndim == 3:
            values = values[:, :, 1]
        means = np.abs(values).mean(axis=0)
    except Exception as exc:
        logger.warning("SHAP global feature importance unavailable: %s", exc)
        means = _fallback_importances(model, feature_names)

    pairs = [
        {"feature": name, "importance": float(value), "contribution": float(value)}
        for name, value in zip(feature_names, means)
    ]
    total = sum(item["importance"] for item in pairs) or 1.0
    for item in pairs:
        normalized = round(item["importance"] / total, 4)
        item["importance"] = normalized
        item["contribution"] = normalized
    return sorted(pairs, key=lambda x: x["importance"], reverse=True)


def compute_player_contributions(model, feature_names, X_background, player_row) -> list:
    """Per-player (local) explanation: how much did THIS player's actual
    stat values push the prediction up or down, relative to the
    background dataset?

    This is what the 'Model contribution' chart on an individual analysis
    result should be driven by. compute_feature_importance() above ignores
    the player's own values entirely and would show identical bars for
    every player — this function does not.

    Args:
        player_row: a single-row array/DataFrame with the same feature
            order as feature_names (e.g. X.iloc[[i]] or a (1, n_features)
            array) for the one player being analyzed.

    Returns a list of dicts with BOTH "contribution" (signed — positive
    means it pushed toward "suspicious", negative means it pushed toward
    "normal") and "importance" (its absolute magnitude, for sorting/sizing
    a chart), plus "player_value", "direction", and "source" so the
    frontend/logs can tell whether this came from real SHAP or the
    fallback proxy.
    """
    row_array = np.asarray(player_row, dtype=float).reshape(-1)
    used_shap = False

    try:
        import shap
        explainer = shap.TreeExplainer(model)
        values = explainer.shap_values(player_row)
        if isinstance(values, list):
            values = values[1] if len(values) > 1 else values[0]
        values = np.asarray(values)
        if values.ndim == 3:
            values = values[:, :, 1]
        row_values = np.asarray(values).reshape(-1)
        used_shap = True
    except Exception as exc:
        logger.warning("Per-player SHAP explanation unavailable: %s", exc)
        # Rough proxy so a SHAP failure doesn't collapse straight to "no
        # signal at all": weight each feature's general importance by how
        # large this specific player's value for it actually is. Still
        # per-player, not a repeated global average and not flat zeros.
        base_importances = _fallback_importances(model, feature_names)
        if row_array.shape[0] != base_importances.shape[0]:
            row_values = np.zeros(len(feature_names))
        else:
            row_values = base_importances * row_array

    pairs = []
    for i, name in enumerate(feature_names):
        value = float(row_values[i]) if i < len(row_values) else 0.0
        player_value = float(row_array[i]) if i < len(row_array) else None
        pairs.append({
            "feature": name,
            "player_value": player_value,
            "contribution": value,
            "importance": abs(value),
            "direction": "increased" if value > 0 else ("decreased" if value < 0 else "no_effect"),
            "source": "shap" if used_shap else "fallback_proxy",
        })

    return sorted(pairs, key=lambda x: x["importance"], reverse=True)