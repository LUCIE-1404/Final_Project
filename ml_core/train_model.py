"""Train and evaluate lecture classifiers using pure Python."""

import csv
import json
import random
from collections import defaultdict
from pathlib import Path

from ml_core.knn import KNearestNeighborClassifier
from ml_core.naive_bayes import (
    MultinomialNaiveBayes,
    accuracy_score,
    classification_report,
    confusion_matrix,
)


PROJECT_ROOT = Path(__file__).resolve().parents[1]
DATASET_PATH = PROJECT_ROOT / "dataset" / "lecture_dataset.csv"
DATASET_EXTRA_PATTERN = "lecture_dataset*.csv"
DIFFICULTY_DATASET_PATH = PROJECT_ROOT / "dataset" / "lecture_difficulty_dataset.csv"
MODEL_PATH = PROJECT_ROOT / "models" / "lecture_topic_classifier.json"
KNN_MODEL_PATH = PROJECT_ROOT / "models" / "lecture_topic_knn_classifier.json"
METRICS_PATH = PROJECT_ROOT / "models" / "lecture_topic_metrics.json"
DIFFICULTY_MODEL_PATH = PROJECT_ROOT / "models" / "lecture_difficulty_classifier.json"
DIFFICULTY_KNN_MODEL_PATH = PROJECT_ROOT / "models" / "lecture_difficulty_knn_classifier.json"
DIFFICULTY_METRICS_PATH = PROJECT_ROOT / "models" / "lecture_difficulty_metrics.json"
RANDOM_SEED = 42
TEST_RATIO = 0.2
ALPHA = 0.5
KNN_VALUES = [3, 5, 7]


def iter_dataset_paths(path=DATASET_PATH):
    path = Path(path)
    if path.is_dir():
        return sorted(path.glob(DATASET_EXTRA_PATTERN))
    dataset_paths = [path]
    dataset_paths.extend(
        sorted(
            candidate
            for candidate in path.parent.glob(DATASET_EXTRA_PATTERN)
            if candidate != path
        )
    )
    return dataset_paths


def load_dataset(path=DATASET_PATH, label_column="label", include_related_files=True):
    rows = []
    dataset_paths = iter_dataset_paths(path) if include_related_files else [Path(path)]
    for dataset_path in dataset_paths:
        with open(dataset_path, "r", encoding="utf-8-sig", newline="") as file:
            reader = csv.DictReader(file)
            for index, row in enumerate(reader, start=2):
                text = (row.get("text") or "").strip()
                label = (row.get(label_column) or "").strip()
                if not text or not label:
                    raise ValueError(f"Invalid empty text/{label_column} at {dataset_path}:{index}")
                rows.append({"text": text, "label": label})

    if not rows:
        raise ValueError("dataset is empty")
    return rows


def stratified_split(rows, test_ratio=TEST_RATIO, seed=RANDOM_SEED):
    grouped_rows = defaultdict(list)
    for row in rows:
        grouped_rows[row["label"]].append(row)

    random_generator = random.Random(seed)
    train_rows = []
    test_rows = []

    for label, label_rows in grouped_rows.items():
        random_generator.shuffle(label_rows)
        test_size = max(1, round(len(label_rows) * test_ratio))
        test_rows.extend(label_rows[:test_size])
        train_rows.extend(label_rows[test_size:])

    random_generator.shuffle(train_rows)
    random_generator.shuffle(test_rows)
    return train_rows, test_rows


def evaluate_classifier(model, test_texts, test_labels, labels):
    predictions = model.predict(test_texts)
    return {
        "accuracy": accuracy_score(test_labels, predictions),
        "confusion_matrix": confusion_matrix(test_labels, predictions, labels),
        "classification_report": classification_report(test_labels, predictions, labels),
    }


def train_classifier(rows, model_path, knn_model_path, metrics_path):
    train_rows, test_rows = stratified_split(rows)

    train_texts = [row["text"] for row in train_rows]
    train_labels = [row["label"] for row in train_rows]
    test_texts = [row["text"] for row in test_rows]
    test_labels = [row["label"] for row in test_rows]
    labels = sorted({row["label"] for row in rows})

    naive_bayes = MultinomialNaiveBayes(alpha=ALPHA)
    naive_bayes.fit(train_texts, train_labels)

    model_comparison = {
        "naive_bayes": {
            "algorithm": "Multinomial Naive Bayes",
            "params": {"alpha": ALPHA},
            **evaluate_classifier(naive_bayes, test_texts, test_labels, labels),
        }
    }

    best_knn = None
    best_knn_name = None
    for k in KNN_VALUES:
        knn = KNearestNeighborClassifier(k=k)
        knn.fit(train_texts, train_labels)
        model_name = f"knn_k{k}"
        model_comparison[model_name] = {
            "algorithm": "K-Nearest Neighbor",
            "params": {"k": k, "distance": "cosine"},
            **evaluate_classifier(knn, test_texts, test_labels, labels),
        }
        if best_knn is None or (
            model_comparison[model_name]["accuracy"]
            > model_comparison[best_knn_name]["accuracy"]
        ):
            best_knn = knn
            best_knn_name = model_name

    selected_model = max(
        model_comparison,
        key=lambda name: (
            model_comparison[name]["accuracy"],
            1 if name == "naive_bayes" else 0,
        ),
    )

    selected_metrics = model_comparison[selected_model]
    metrics = {
        "dataset_size": len(rows),
        "train_size": len(train_rows),
        "test_size": len(test_rows),
        "labels": labels,
        "selected_model": selected_model,
        "selected_algorithm": selected_metrics["algorithm"],
        "accuracy": selected_metrics["accuracy"],
        "confusion_matrix": selected_metrics["confusion_matrix"],
        "classification_report": selected_metrics["classification_report"],
        "model_comparison": model_comparison,
    }

    MODEL_PATH.parent.mkdir(parents=True, exist_ok=True)
    model_path.parent.mkdir(parents=True, exist_ok=True)
    naive_bayes.save(model_path)
    if best_knn is not None:
        best_knn.save(knn_model_path)
    with open(metrics_path, "w", encoding="utf-8") as file:
        json.dump(metrics, file, ensure_ascii=False, indent=2)

    return metrics


def train():
    topic_rows = load_dataset()
    difficulty_rows = load_dataset(
        DIFFICULTY_DATASET_PATH,
        label_column="difficulty",
        include_related_files=False,
    )
    return {
        "topic": train_classifier(topic_rows, MODEL_PATH, KNN_MODEL_PATH, METRICS_PATH),
        "difficulty": train_classifier(
            difficulty_rows,
            DIFFICULTY_MODEL_PATH,
            DIFFICULTY_KNN_MODEL_PATH,
            DIFFICULTY_METRICS_PATH,
        ),
    }


def print_metrics(name, metrics):
    print(f"=== Lecture {name.title()} Classifier ===")
    print(f"Dataset size: {metrics['dataset_size']}")
    print(f"Train size: {metrics['train_size']}")
    print(f"Test size: {metrics['test_size']}")
    print(f"Selected model: {metrics['selected_model']} ({metrics['selected_algorithm']})")
    print(f"Selected accuracy: {metrics['accuracy']:.2%}")
    print("")
    print("Model comparison:")
    for model_name, model_metrics in metrics["model_comparison"].items():
        params = ", ".join(
            f"{key}={value}"
            for key, value in model_metrics["params"].items()
        )
        print(f"- {model_name}: {model_metrics['accuracy']:.2%} ({params})")
    print("")
    print("Confusion matrix:")
    labels = metrics["labels"]
    print("actual\\predicted," + ",".join(labels))
    for actual in labels:
        row = [str(metrics["confusion_matrix"][actual][predicted]) for predicted in labels]
        print(actual + "," + ",".join(row))
    print("")


if __name__ == "__main__":
    all_metrics = train()
    for classifier_name, classifier_metrics in all_metrics.items():
        print_metrics(classifier_name, classifier_metrics)
        print("")
