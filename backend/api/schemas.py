from typing import Any, Dict, List, Optional
from pydantic import BaseModel

class HealthResponse(BaseModel):
    status: str
    model_loaded: bool
    model_name: Optional[str]
    feature_count: Optional[int]

class ExtractedStat(BaseModel):
    name: str
    value: Optional[float]
    raw: Optional[str]
    confidence: float
    source: str

class ExtractedStats(BaseModel):
    mode: Optional[str]
    stats: List[ExtractedStat]
    warnings: List[str]

class EvidenceItem(BaseModel):
    feature: str
    player_value: Optional[float]
    legit_range: Optional[str]
    indicator: str
    contribution: float
    explanation: str

class AnalysisResult(BaseModel):
    verdict: str = "prediction"
    suspicion_score: float
    risk_level: str
    risk_color: str
    model_confidence: Optional[float]
    prediction_label: str
    probability: float
    message: Optional[str] = None
    extracted_stats: ExtractedStats
    evidence: List[EvidenceItem]
    feature_importance: List[Dict[str, Any]]
    disclaimer: str
    model_info: Dict[str, Any]

class ModelInfoResponse(BaseModel):
    model_name: str
    metrics: Dict[str, Any]
    feature_importance: List[Dict[str, Any]]
    confusion_matrix: List[List[int]]
    dataset_summary: Dict[str, Any]
    is_experimental: bool