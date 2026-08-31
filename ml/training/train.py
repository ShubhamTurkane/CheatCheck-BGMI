import argparse
import json
import logging
import sys
from pathlib import Path

import joblib
from sklearn.ensemble import RandomForestClassifier, GradientBoostingClassifier
from sklearn.linear_model import LogisticRegression
from sklearn.model_selection import train_test_split
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import StandardScaler
from sklearn.metrics import f1_score, roc_auc_score
from sklearn.svm import SVC

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))

from ml.preprocessing.data_loader import load_dataset, FEATURE_COLUMNS
from ml.evaluation.evaluate import evaluate_model
from ml.explainability.shap_explainer import compute_feature_importance

logging.basicConfig(level=logging.INFO, format="%(levelname)s | %(message)s")

SAVED_DIR = ROOT / "ml" / "saved_models"
SAVED_DIR.mkdir(parents=True, exist_ok=True)

def build_models():
    models = {
        "LogisticRegression": Pipeline([
            ("scale", StandardScaler()),
            ("model", LogisticRegression(max_iter=1500, class_weight="balanced")),
        ]),
        "RandomForest": RandomForestClassifier(
            n_estimators=350, max_depth=14,
            class_weight="balanced", random_state=42, n_jobs=-1
        ),
        "GradientBoosting": GradientBoostingClassifier(random_state=42),
        "SVM": Pipeline([
            ("scale", StandardScaler()),
            ("model", SVC(probability=True, class_weight="balanced", random_state=42)),
        ]),
    }
    try:
        from xgboost import XGBClassifier
        models["XGBoost"] = XGBClassifier(
            n_estimators=300,
            max_depth=6,
            learning_rate=0.08,
            subsample=0.9,
            colsample_bytree=0.9,
            eval_metric="logloss",
            random_state=42,
            n_jobs=4,
        )
    except Exception:
        pass
    return models

def train(data_path: str):
    df, dataset_summary = load_dataset(data_path)
    missing_features = [f for f in FEATURE_COLUMNS if f not in df.columns]
    if missing_features:
        raise ValueError(f"Dataset is missing required features: {missing_features}")

    X = df[FEATURE_COLUMNS].astype(float)
    y = df["Label"].astype(int)

    X_train, X_test, y_train, y_test = train_test_split(
        X, y, test_size=0.2, stratify=y, random_state=42
    )

    candidates = []
    for name, model in build_models().items():
        model.fit(X_train, y_train)
        pred = model.predict(X_test)
        proba = model.predict_proba(X_test)[:, 1]
        metrics = evaluate_model(y_test, pred, proba, name)
        candidates.append((name, model, metrics))
        logging.info("%s: F1=%.4f ROC-AUC=%.4f Precision=%.4f Recall=%.4f",
                     name, metrics["f1"], metrics["roc_auc"],
                     metrics["precision"], metrics["recall"])

    candidates.sort(key=lambda item: (item[2]["f1"], item[2]["roc_auc"]), reverse=True)
    best_name, best_model, best_metrics = candidates[0]

    # Refit the selected model on the full training split only; the held-out test set remains untouched.
    feature_importance = compute_feature_importance(
        best_model,
        FEATURE_COLUMNS,
        X_train.sample(min(250, len(X_train)), random_state=42)
    )

    joblib.dump(best_model, SAVED_DIR / "model.pkl")
    # Kept for compatibility with the scaffold; the trained estimators already contain their scaler when needed.
    joblib.dump(None, SAVED_DIR / "scaler.pkl")

    best_metrics.update({
        "model_name": best_name,
        "is_experimental": True,
        "tested_on_holdout": True,
        "selection_rule": "highest F1, ROC-AUC as tie-breaker",
        "tested_candidates": [
            {"model_name": name, **metrics} for name, _, metrics in candidates
        ],
    })
    (SAVED_DIR / "metrics.json").write_text(json.dumps(best_metrics, indent=2), encoding="utf-8")
    (SAVED_DIR / "feature_importance.json").write_text(
        json.dumps(feature_importance, indent=2), encoding="utf-8"
    )
    (SAVED_DIR / "dataset_summary.json").write_text(
        json.dumps(dataset_summary, indent=2), encoding="utf-8"
    )

    # Persist a small background matrix for optional future SHAP workflows.
    X_train.head(100).to_json(SAVED_DIR / "shap_background.json", orient="split")
    return best_metrics

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--data", default=str(ROOT / "ml" / "dataset" / "BGMI_Career_Stats_Training_Data.xlsx"))
    args = parser.parse_args()
    train(args.data)
