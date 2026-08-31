import os
from pathlib import Path
from dotenv import load_dotenv

load_dotenv()

BASE_DIR = Path(__file__).resolve().parent.parent
PROJECT_ROOT = BASE_DIR.parent

APP_NAME = os.getenv("APP_NAME", "CheatCheck BGMI")
ALLOWED_ORIGINS = [x.strip() for x in os.getenv(
    "ALLOWED_ORIGINS",
    "http://localhost:5173,http://127.0.0.1:5173"
).split(",") if x.strip()]
MAX_UPLOAD_MB = int(os.getenv("MAX_UPLOAD_MB", "10"))

def _resolve_project_path(value: str) -> Path:
    p = Path(value)
    return p if p.is_absolute() else (BASE_DIR / p).resolve()

MODEL_DIR = _resolve_project_path(os.getenv("MODEL_DIR", "../ml/saved_models"))
DATASET_PATH = _resolve_project_path(
    os.getenv("DATASET_PATH", "../ml/dataset/BGMI_Career_Stats_Training_Data.xlsx")
)
TEMP_DIR = _resolve_project_path(os.getenv("TEMP_DIR", "./tmp_uploads"))
TEMP_DIR.mkdir(parents=True, exist_ok=True)

DISCLAIMER_TEXT = (
    "CheatCheck BGMI provides an AI-based statistical assessment. "
    "It cannot definitively prove whether a player is cheating. "
    "Results may contain false positives or false negatives."
)

RISK_THRESHOLDS = {
    "likely_legit": (0, 30),
    "suspicious": (30, 60),
    "highly_suspicious": (60, 80),
    "extremely_suspicious": (80, 100),
}

RISK_COLORS = {
    "likely_legit": "#2E8B57",
    "suspicious": "#D99000",
    "highly_suspicious": "#D64545",
    "extremely_suspicious": "#8B0000",
}

MODE_BENCHMARKS = {
    "Solo": {"accuracy": (10, 26), "headshot": (12, 30)},
    "Duo": {"accuracy": (8, 24), "headshot": (12, 30)},
    "Squad": {"accuracy": (6, 22), "headshot": (12, 30)},
}

MODEL_FEATURES = [
    "Matches_Played", "Wins", "Top10_Finishes", "Total_Kills",
    "Highest_Kills_Single_Match", "Total_Damage", "Headshot_Kills",
    "Shots_Fired", "Shots_Hit", "Total_Assists", "Win_Ratio",
    "Top10_Ratio", "KD_Ratio", "Avg_Kills_Per_Match",
    "Avg_Damage_Per_Match", "Headshot_Ratio", "Accuracy", "Mode_Code",
]

OCR_TARGET_STATS = [x for x in MODEL_FEATURES if x != "Mode_Code"]
