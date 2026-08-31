from sklearn.metrics import (
    accuracy_score, precision_score, recall_score,
    f1_score, roc_auc_score, confusion_matrix
)

def evaluate_model(y_true, y_pred, y_proba, model_name: str) -> dict:
    return {
        "model_name": model_name,
        "accuracy": float(accuracy_score(y_true, y_pred)),
        "precision": float(precision_score(y_true, y_pred, zero_division=0)),
        "recall": float(recall_score(y_true, y_pred, zero_division=0)),
        "f1": float(f1_score(y_true, y_pred, zero_division=0)),
        "roc_auc": float(roc_auc_score(y_true, y_proba)) if len(set(y_true)) > 1 else 0.0,
        "confusion_matrix": confusion_matrix(y_true, y_pred).tolist(),
    }
