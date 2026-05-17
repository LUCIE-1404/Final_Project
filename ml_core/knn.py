"""K-Nearest Neighbor text classifier implemented with the Python standard library."""

import json
import math
from collections import Counter

from ml_core.preprocess import count_tokens


class KNearestNeighborClassifier:
    """KNN classifier using cosine similarity over bag-of-words vectors."""

    def __init__(self, k=5):
        if k <= 0:
            raise ValueError("k must be greater than 0")
        self.k = k
        self.labels = []
        self.train_labels = []
        self.train_vectors = []
        self.train_norms = []
        self.class_counts = Counter()

    def fit(self, texts, labels):
        if len(texts) != len(labels):
            raise ValueError("texts and labels must have the same length")
        if not texts:
            raise ValueError("training data is empty")

        self.train_labels = []
        self.train_vectors = []
        self.train_norms = []
        self.class_counts = Counter()

        for text, label in zip(texts, labels):
            if not label:
                raise ValueError("label cannot be empty")

            vector = count_tokens(text)
            self.train_vectors.append(vector)
            self.train_norms.append(self._norm(vector))
            self.train_labels.append(label)
            self.class_counts[label] += 1

        self.labels = sorted(self.class_counts)
        return self

    @staticmethod
    def _norm(vector):
        return math.sqrt(sum(value * value for value in vector.values()))

    @staticmethod
    def _cosine_similarity(left, left_norm, right, right_norm):
        if not left_norm or not right_norm:
            return 0.0

        if len(left) > len(right):
            left, right = right, left

        dot_product = sum(value * right.get(token, 0) for token, value in left.items())
        return dot_product / (left_norm * right_norm)

    def _neighbors(self, text):
        if not self.train_vectors:
            raise ValueError("model has not been trained")

        vector = count_tokens(text)
        norm = self._norm(vector)
        scored_neighbors = []

        for train_vector, train_norm, label in zip(
            self.train_vectors,
            self.train_norms,
            self.train_labels,
        ):
            similarity = self._cosine_similarity(vector, norm, train_vector, train_norm)
            scored_neighbors.append((similarity, label))

        scored_neighbors.sort(key=lambda item: (-item[0], item[1]))
        return scored_neighbors[: min(self.k, len(scored_neighbors))]

    def predict_proba(self, text):
        neighbors = self._neighbors(text)
        votes = {label: 0.0 for label in self.labels}

        for similarity, label in neighbors:
            votes[label] += similarity if similarity > 0 else 1e-12

        total = sum(votes.values())
        if total == 0:
            sample_count = sum(self.class_counts.values())
            return {
                label: self.class_counts[label] / sample_count
                for label in self.labels
            }

        return {label: votes[label] / total for label in self.labels}

    def predict_one(self, text):
        probabilities = self.predict_proba(text)
        return max(probabilities, key=probabilities.get)

    def predict(self, texts):
        return [self.predict_one(text) for text in texts]

    def to_dict(self):
        return {
            "k": self.k,
            "labels": self.labels,
            "train_labels": self.train_labels,
            "train_vectors": [dict(vector) for vector in self.train_vectors],
            "train_norms": self.train_norms,
            "class_counts": dict(self.class_counts),
        }

    @classmethod
    def from_dict(cls, data):
        model = cls(k=data["k"])
        model.labels = list(data["labels"])
        model.train_labels = list(data["train_labels"])
        model.train_vectors = [Counter(vector) for vector in data["train_vectors"]]
        model.train_norms = list(data["train_norms"])
        model.class_counts = Counter(data["class_counts"])
        return model

    def save(self, path):
        with open(path, "w", encoding="utf-8") as file:
            json.dump(self.to_dict(), file, ensure_ascii=False, indent=2)

    @classmethod
    def load(cls, path):
        with open(path, "r", encoding="utf-8") as file:
            return cls.from_dict(json.load(file))
