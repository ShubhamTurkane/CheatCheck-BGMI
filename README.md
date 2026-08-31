# CheatCheck BGMI

CheatCheck BGMI is a full-stack prototype for statistical risk assessment of BGMI career-statistics screenshots.

> **Important:** this application does not prove cheating. It produces an ML-based statistical suspicion/risk assessment and can have false positives and false negatives. It is not affiliated with Krafton or BGMI.

## Project structure

- `frontend/` — React + Vite + Tailwind dashboard
- `backend/` — FastAPI API, OCR, inference and explainability
- `ml/` — dataset loading, training, evaluation and saved-model artifacts
- `tests/` — backend tests

## Dataset

Place the supplied dataset at:

`ml/dataset/BGMI_Career_Stats_Training_Data.xlsx`

The trainer expects a sheet containing fields such as:

`Mode, Matches_Played, Wins, Top10_Finishes, Total_Kills, Highest_Kills_Single_Match, Total_Damage, Headshot_Kills, Shots_Fired, Shots_Hit, Total_Assists, Win_Ratio, Top10_Ratio, KD_Ratio, Avg_Kills_Per_Match, Avg_Damage_Per_Match, Headshot_Ratio, Accuracy, Label`

The code parses percentage strings such as `11.8%`, checks duplicates, reports missing values, handles the 3:1 class imbalance using class weights where supported, and selects a model using validation F1 with ROC-AUC as a secondary criterion.

## Backend setup

Python 3.10/3.11 is recommended.

```bash
cd backend
python -m venv .venv
# Windows:
.venv\Scripts\activate
# macOS/Linux:
# source .venv/bin/activate

pip install -r requirements.txt
cd ..
python -m ml.training.train
cd backend
uvicorn main:app --reload --port 8000
```

The API is available at `http://localhost:8000` and Swagger docs at `http://localhost:8000/docs`.

## Frontend setup

```bash
cd frontend
npm install
npm run dev
```

Open `http://localhost:5173`.

Create `frontend/.env` from `.env.example` if the API is not running at the default URL.

## Retraining

```bash
python -m ml.training.train --data ml/dataset/BGMI_Career_Stats_Training_Data.xlsx
```

Artifacts are written to `ml/saved_models/`.

## Notes

- The OCR layer is deliberately conservative. It reports missing values rather than inventing them.
- Production inference should ideally use an OCR layout/parser tuned to the actual BGMI screenshot format.
- The dashboard only shows cheat categories if the dataset supplies category labels. A binary Legit/Hacker label does not identify wallhack, ESP, aimbot, etc.
- The sample dataset is not included in this ZIP because the uploaded file contained only the project/code instructions, not the actual XLSX bytes.
