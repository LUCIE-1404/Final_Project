"""Prediction helpers for the lecture topic classifier."""

import json
from pathlib import Path

from ml_core.knn import KNearestNeighborClassifier
from ml_core.naive_bayes import MultinomialNaiveBayes


PROJECT_ROOT = Path(__file__).resolve().parents[1]
DEFAULT_MODEL_PATH = PROJECT_ROOT / "models" / "lecture_topic_classifier.json"
DEFAULT_KNN_MODEL_PATH = PROJECT_ROOT / "models" / "lecture_topic_knn_classifier.json"
DEFAULT_METRICS_PATH = PROJECT_ROOT / "models" / "lecture_topic_metrics.json"


def load_model_metrics(path=DEFAULT_METRICS_PATH):
    path = Path(path)
    if not path.exists():
        return {}
    with open(path, "r", encoding="utf-8") as file:
        return json.load(file)


def load_topic_classifier(path=DEFAULT_MODEL_PATH):
    metrics = load_model_metrics()
    selected_model = metrics.get("selected_model", "naive_bayes")

    if selected_model.startswith("knn") and DEFAULT_KNN_MODEL_PATH.exists():
        return KNearestNeighborClassifier.load(DEFAULT_KNN_MODEL_PATH), selected_model

    if not Path(path).exists():
        return None
    return MultinomialNaiveBayes.load(path), "naive_bayes"


def predict_topic(text, model=None):
    if model is None:
        loaded = load_topic_classifier()
        if loaded is None:
            classifier = None
            algorithm = "unknown"
        else:
            classifier, algorithm = loaded
    else:
        classifier = model
        algorithm = model.__class__.__name__

    if classifier is None:
        return {
            "label": "unknown",
            "confidence": 0.0,
            "probabilities": {},
            "model_available": False,
            "algorithm": algorithm,
        }

    probabilities = classifier.predict_proba(text)
    label = max(probabilities, key=probabilities.get)
    return {
        "label": label,
        "confidence": probabilities[label],
        "probabilities": probabilities,
        "model_available": True,
        "algorithm": algorithm,
    }
