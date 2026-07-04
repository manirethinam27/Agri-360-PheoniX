from __future__ import annotations

import numpy as np
import pandas as pd
from sklearn.ensemble import RandomForestClassifier
from sklearn.metrics import accuracy_score, classification_report, confusion_matrix
from sklearn.model_selection import train_test_split
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import StandardScaler

FEATURES = ["day_norm", "observed_ndvi", "observed_ndmi", "ndvi_slope", "ndmi_slope"]


def _feature_frame(df: pd.DataFrame) -> pd.DataFrame:
    clear = df.dropna(subset=["observed_ndvi", "observed_ndmi"]).copy().sort_values(["plot_id", "day"])
    clear["ndvi_slope"] = clear.groupby("plot_id")["observed_ndvi"].diff().fillna(0.0)
    clear["ndmi_slope"] = clear.groupby("plot_id")["observed_ndmi"].diff().fillna(0.0)
    clear[FEATURES] = clear[FEATURES].replace([np.inf, -np.inf], np.nan).fillna(0.0)
    return clear


def _matrix_payload(y_true, y_pred, labels: list[str]) -> dict:
    cm = confusion_matrix(y_true, y_pred, labels=labels)
    return {"labels": labels, "matrix": cm.tolist(), "total": int(cm.sum())}


def train_classifier(df: pd.DataFrame, target: str, labels: list[str]) -> dict:
    features = _feature_frame(df)
    if features[target].nunique() < 2 or len(features) < 20:
        return {
            "target": target,
            "accuracy": 0.0,
            "labels": labels,
            "confusion_matrix": {"labels": labels, "matrix": [], "total": 0},
            "classification_report": {},
            "feature_count": int(len(features)),
            "model": "RandomForestClassifier",
            "warning": "Not enough clear observations to train a reliable classifier.",
        }
    stratify = features[target] if features[target].value_counts().min() >= 2 else None
    train, test = train_test_split(features, test_size=0.28, random_state=42, stratify=stratify)
    model = Pipeline(
        [
            ("scale", StandardScaler()),
            ("rf", RandomForestClassifier(n_estimators=180, max_depth=12, min_samples_leaf=3, class_weight="balanced_subsample", random_state=42)),
        ]
    )
    model.fit(train[FEATURES], train[target])
    pred = model.predict(test[FEATURES])
    present_labels = [label for label in labels if label in set(features[target])]
    return {
        "target": target,
        "accuracy": round(float(accuracy_score(test[target], pred)), 4),
        "labels": present_labels,
        "confusion_matrix": _matrix_payload(test[target], pred, present_labels),
        "classification_report": classification_report(test[target], pred, labels=present_labels, output_dict=True, zero_division=0),
        "feature_count": int(len(features)),
        "model": "RandomForestClassifier",
        "features_used": FEATURES,
        "training_disclosure": "Features are observed NDVI/NDMI time-series values after revisit/cloud/noise simulation; clean true_* values are excluded.",
    }


def train_all(df: pd.DataFrame) -> dict:
    return {
        "crop_classifier": train_classifier(df, "crop", ["Rice", "Wheat", "Cotton", "Sugarcane"]),
        "growth_stage_predictor": train_classifier(df, "growth_stage", ["Initial", "Development", "Mid-season", "Late-season"]),
    }
