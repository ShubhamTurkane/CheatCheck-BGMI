import logging
from pathlib import Path
from typing import Tuple

import pandas as pd

logger = logging.getLogger(__name__)

PERCENT_COLS = [
    "Win_Ratio", "Top10_Ratio", "Headshot_Ratio", "Accuracy"
]

EXPECTED_COLS = [
    "Mode", "Matches_Played", "Wins", "Top10_Finishes", "Total_Kills",
    "Highest_Kills_Single_Match", "Total_Damage", "Headshot_Kills",
    "Shots_Fired", "Shots_Hit", "Total_Assists", "Win_Ratio",
    "Top10_Ratio", "KD_Ratio", "Avg_Kills_Per_Match",
    "Avg_Damage_Per_Match", "Headshot_Ratio", "Accuracy", "Label"
]

FEATURE_COLUMNS = [
    "Matches_Played", "Wins", "Top10_Finishes", "Total_Kills",
    "Highest_Kills_Single_Match", "Total_Damage", "Headshot_Kills",
    "Shots_Fired", "Shots_Hit", "Total_Assists", "Win_Ratio",
    "Top10_Ratio", "KD_Ratio", "Avg_Kills_Per_Match",
    "Avg_Damage_Per_Match", "Headshot_Ratio", "Accuracy", "Mode_Code",
]

def _parse_percent(value):
    if pd.isna(value):
        return None
    if isinstance(value, str):
        return float(value.strip().replace("%", "").replace(",", ""))
    return float(value)

def load_dataset(path: str | Path) -> Tuple[pd.DataFrame, dict]:
    path = Path(path)
    if not path.exists():
        raise FileNotFoundError(
            f"Dataset not found: {path}. Place BGMI_Career_Stats_Training_Data.xlsx in ml/dataset/."
        )

    book = pd.ExcelFile(path)
    sheet = "Training_Data" if "Training_Data" in book.sheet_names else book.sheet_names[0]
    df = pd.read_excel(path, sheet_name=sheet)
    df.columns = [str(c).strip() for c in df.columns]

    if "Label" not in df.columns:
        raise ValueError("Dataset must contain a Label column.")
    label_text = df["Label"].astype(str).str.strip().str.lower()
    mapping = {"legit": 0, "hacker": 1, "cheater": 1, "suspicious": 1}
    unknown = sorted(set(label_text) - set(mapping))
    if unknown:
        raise ValueError(f"Label column has unsupported values: {unknown}")
    df["Label"] = label_text.map(mapping).astype(int)

    for column in PERCENT_COLS:
        if column in df.columns:
            df[column] = df[column].map(_parse_percent)

    for column in EXPECTED_COLS:
        if column in df.columns and column not in {"Label", "Mode"}:
            df[column] = pd.to_numeric(df[column], errors="coerce")

    if "Mode" not in df.columns:
        raise ValueError("Dataset must contain a Mode column.")
    df["Mode"] = df["Mode"].astype(str).str.title()
    df["Mode_Code"] = df["Mode"].map({"Solo": 0, "Duo": 1, "Squad": 2}).fillna(-1).astype(int)

    critical = [c for c in ["Accuracy", "Headshot_Ratio", "KD_Ratio", "Label", "Mode"] if c in df.columns]
    df = df.dropna(subset=critical).copy()

    missing = {c: int(df[c].isna().sum()) for c in EXPECTED_COLS if c in df.columns}
    duplicates = int(df.duplicated().sum())

    summary = {
        "sheet": sheet,
        "total_records": int(len(df)),
        "legit_count": int((df["Label"] == 0).sum()),
        "hacker_count": int((df["Label"] == 1).sum()),
        "class_balance": float(df["Label"].mean()),
        "missing_values": {k: v for k, v in missing.items() if v > 0},
        "duplicates": duplicates,
        "columns": list(df.columns),
    }

    if "Total_Assists" in df.columns:
        solo_bad = (
            (df["Mode"].str.lower() == "solo") &
            (df["Total_Assists"].fillna(0) > 0)
        )
        summary["solo_assists_integrity_issues"] = int(solo_bad.sum())

    logger.info("Dataset summary: %s", summary)
    return df, summary
