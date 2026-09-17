from pathlib import Path
import joblib
import numpy as np
from sklearn.ensemble import RandomForestClassifier, RandomForestRegressor, IsolationForest

MODEL_DIR = Path(__file__).resolve().parent / "artifacts"
MODEL_DIR.mkdir(parents=True, exist_ok=True)
FEATURES = ["duration_min","task_switches","completed","difficulty","help_requests","hour"]

def train_behavior_model(df):
    model = RandomForestClassifier(
        n_estimators=220, max_depth=9, random_state=42, class_weight="balanced"
    )
    model.fit(df[FEATURES], df["task_type"])
    joblib.dump(model, MODEL_DIR/"behavior_model.joblib")
    return model

def train_progress_model(df):
    work = df.copy()
    work["quality"] = (
        work.completed*.55 +
        np.clip(work.duration_min/120,0,1)*.20 +
        np.clip(1-work.task_switches/10,0,1)*.15 +
        np.clip(1-work.help_requests/5,0,1)*.10
    )
    model = RandomForestRegressor(n_estimators=180,max_depth=8,random_state=42)
    model.fit(work[FEATURES],work["quality"])
    joblib.dump(model,MODEL_DIR/"progress_model.joblib")
    return model

def train_drift_model(df):
    model = IsolationForest(contamination=.12,random_state=42)
    model.fit(df[FEATURES])
    joblib.dump(model,MODEL_DIR/"drift_model.joblib")
    return model

def load_models():
    b = MODEL_DIR/"behavior_model.joblib"
    p = MODEL_DIR/"progress_model.joblib"
    return (
        joblib.load(b) if b.exists() else None,
        joblib.load(p) if p.exists() else None
    )

def load_drift_model():
    p = MODEL_DIR/"drift_model.joblib"
    return joblib.load(p) if p.exists() else None
