from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from utils.config import APP_NAME, ALLOWED_ORIGINS
from api.routes import router
from models.predictor import ModelPredictor
from models.explainer import ModelExplainer

@asynccontextmanager
async def lifespan(app: FastAPI):
    predictor = ModelPredictor()
    predictor.load()

    explainer = ModelExplainer()
    if predictor.is_loaded:
        explainer.load(predictor.model, predictor.feature_names)

    app.state.predictor = predictor
    app.state.explainer = explainer
    yield

app = FastAPI(
    title=APP_NAME,
    description="AI-powered statistical analysis for BGMI player behavior.",
    version="1.0.0",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=ALLOWED_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(router, prefix="/api")

@app.get("/")
def root():
    return {"app": APP_NAME, "docs": "/docs", "health": "/api/health"}
