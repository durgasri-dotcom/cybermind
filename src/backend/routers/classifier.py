from __future__ import annotations
import pickle
import os
import numpy as np
from fastapi import APIRouter
from pydantic import BaseModel

router = APIRouter()

MODEL_PATH = "data/gold/models/threat_classifier.pkl"
_model_data = None

def _load_model():
    global _model_data
    if _model_data is None and os.path.exists(MODEL_PATH):
        with open(MODEL_PATH, "rb") as f:
            _model_data = pickle.load(f)
    return _model_data

class ThreatInput(BaseModel):
    cvss_score: float
    risk_score: float = 0.5
    description: str = ""

class PredictionResponse(BaseModel):
    predicted_severity: str
    confidence: float
    probabilities: dict
    auc: float
    model_version: str = "gradient_boosting_v1"

@router.post("/classifier/predict")
async def predict_severity(body: ThreatInput) -> PredictionResponse:
    model_data = _load_model()
    if model_data is None:
        return PredictionResponse(
            predicted_severity="UNKNOWN",
            confidence=0.0,
            probabilities={},
            auc=0.0,
        )
    clf = model_data["model"]
    le = model_data["label_encoder"]
    feature_cols = model_data["feature_cols"]
    desc = body.description.lower()
    features = {
        "cvss_score": body.cvss_score,
        "risk_score": body.risk_score,
        "has_rce": int("remote code execution" in desc or "rce" in desc),
        "has_sqli": int("sql injection" in desc),
        "has_overflow": int("buffer overflow" in desc or "overflow" in desc),
        "has_privesc": int("privilege escalation" in desc),
        "has_ransomware": int("ransomware" in desc),
        "has_auth_bypass": int("authentication bypass" in desc),
        "has_xss": int("cross-site scripting" in desc or "xss" in desc),
        "desc_length": len(desc),
        "num_cwe": 1,
        "num_mitre": 1,
    }
    X = np.array([[features[c] for c in feature_cols]])
    proba = clf.predict_proba(X)[0]
    pred_idx = np.argmax(proba)
    predicted = le.inverse_transform([pred_idx])[0]
    probs = {le.classes_[i]: round(float(proba[i]), 4) for i in range(len(le.classes_))}
    return PredictionResponse(
        predicted_severity=predicted,
        confidence=round(float(proba[pred_idx]), 4),
        probabilities=probs,
        auc=round(model_data.get("auc", 0.0), 4),
    )

@router.get("/classifier/info")
async def model_info():
    model_data = _load_model()
    if model_data is None:
        return {"status": "model_not_found"}
    return {
        "status": "ready",
        "auc": round(model_data.get("auc", 0.0), 4),
        "cv_f1_mean": round(model_data.get("cv_f1_mean", 0.0), 4),
        "cv_f1_std": round(model_data.get("cv_f1_std", 0.0), 4),
        "classes": model_data.get("classes", []),
        "num_training_samples": model_data.get("num_training_samples", 0),
        "model_version": "gradient_boosting_v1",
        "features": model_data.get("feature_cols", []),
    }