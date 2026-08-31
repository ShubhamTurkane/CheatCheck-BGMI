import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "backend"))
from fastapi.testclient import TestClient
from backend.main import app

def test_root():
    with TestClient(app) as client:
        response = client.get("/")
        assert response.status_code == 200
        assert response.json()["app"] == "CheatCheck BGMI"

def test_health():
    with TestClient(app) as client:
        response = client.get("/api/health")
        assert response.status_code == 200
        assert response.json()["status"] == "ok"
