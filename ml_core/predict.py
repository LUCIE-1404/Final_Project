"""Prediction helpers for the lecture topic classifier."""

import json
from pathlib import Path

from ml_core.knn import KNearestNeighborClassifier
from ml_core.naive_bayes import MultinomialNaiveBayes


PROJECT_ROOT = Path(__file__).resolve().parents[1]
DEFAULT_MODEL_PATH = PROJECT_ROOT / "models" / "lecture_topic_classifier.json"
DEFAULT_KNN_MODEL_PATH = PROJECT_ROOT / "models" / "lecture_topic_knn_classifier.json"
DEFAULT_METRICS_PATH = PROJECT_ROOT / "models" / "lecture_topic_metrics.json"
DEFAULT_DIFFICULTY_MODEL_PATH = PROJECT_ROOT / "models" / "lecture_difficulty_classifier.json"
DEFAULT_DIFFICULTY_KNN_MODEL_PATH = PROJECT_ROOT / "models" / "lecture_difficulty_knn_classifier.json"
DEFAULT_DIFFICULTY_METRICS_PATH = PROJECT_ROOT / "models" / "lecture_difficulty_metrics.json"


def load_model_metrics(path=DEFAULT_METRICS_PATH):
    path = Path(path)
    if not path.exists():
        return {}
    with open(path, "r", encoding="utf-8") as file:
        return json.load(file)


def load_topic_classifier(path=DEFAULT_MODEL_PATH):
    return load_classifier(
        model_path=path,
        knn_model_path=DEFAULT_KNN_MODEL_PATH,
        metrics_path=DEFAULT_METRICS_PATH,
    )


def load_difficulty_classifier(path=DEFAULT_DIFFICULTY_MODEL_PATH):
    return load_classifier(
        model_path=path,
        knn_model_path=DEFAULT_DIFFICULTY_KNN_MODEL_PATH,
        metrics_path=DEFAULT_DIFFICULTY_METRICS_PATH,
    )


def load_classifier(model_path, knn_model_path, metrics_path):
    metrics = load_model_metrics(metrics_path)
    selected_model = metrics.get("selected_model", "naive_bayes")
    knn_model_path = Path(knn_model_path)
    if selected_model.startswith("knn") and knn_model_path.exists():
        return KNearestNeighborClassifier.load(knn_model_path), selected_model

    model_path = Path(model_path)
    if not model_path.exists():
        return None
    return MultinomialNaiveBayes.load(model_path), "naive_bayes"


def predict_topic(text, model=None):
    return predict_with_classifier(text, load_topic_classifier, model)


def predict_difficulty(text, model=None):
    return predict_with_classifier(text, load_difficulty_classifier, model)


def predict_with_classifier(text, loader, model=None):
    if model is None:
        loaded = loader()
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
