"""Multinomial Naive Bayes implemented with the Python standard library."""

import json
import math
from collections import Counter, defaultdict

from ml_core.preprocess import count_tokens


class MultinomialNaiveBayes:
    """Bag-of-words Multinomial Naive Bayes classifier."""

    def __init__(self, alpha=1.0):
        if alpha <= 0:
            raise ValueError("alpha must be greater than 0")
        self.alpha = alpha
        self.labels = []
        self.vocabulary = set()
        self.class_doc_counts = Counter()
        self.class_token_counts = defaultdict(Counter)
        self.class_total_tokens = Counter()
        self.total_docs = 0

    def fit(self, texts, labels):
        if len(texts) != len(labels):
            raise ValueError("texts and labels must have the same length")
        if not texts:
            raise ValueError("training data is empty")

        self.labels = []
        self.vocabulary = set()
        self.class_doc_counts = Counter()
        self.class_token_counts = defaultdict(Counter)
        self.class_total_tokens = Counter()
        self.total_docs = len(texts)

        for text, label in zip(texts, labels):
            if not label:
                raise ValueError("label cannot be empty")

            if label not in self.class_doc_counts:
                self.labels.append(label)

            token_counts = count_tokens(text)
            self.class_doc_counts[label] += 1
            self.class_token_counts[label].update(token_counts)
            self.class_total_tokens[label] += sum(token_counts.values())
            self.vocabulary.update(token_counts)

        if not self.vocabulary:
            raise ValueError("training vocabulary is empty")

        self.labels.sort()
        return self

    def _label_log_probability(self, token_counts, label):
        vocab_size = len(self.vocabulary)
        prior = self.class_doc_counts[label] / self.total_docs
        score = math.log(prior)
        denominator = self.class_total_tokens[label] + self.alpha * vocab_size

        for token, count in token_counts.items():
            if token not in self.vocabulary:
                continue
            numerator = self.class_token_counts[label][token] + self.alpha
            score += count * math.log(numerator / denominator)

        return score

    def predict_log_scores(self, text):
        if not self.labels:
            raise ValueError("model has not been trained")

        token_counts = count_tokens(text)
        return {
            label: self._label_log_probability(token_counts, label)
            for label in self.labels
        }

    def predict_proba(self, text):
        log_scores = self.predict_log_scores(text)
        max_log_score = max(log_scores.values())
        exp_scores = {
            label: math.exp(score - max_log_score)
            for label, score in log_scores.items()
        }
        total = sum(exp_scores.values())
        return {
            label: exp_scores[label] / total
            for label in sorted(exp_scores)
        }

    def predict_one(self, text):
        probabilities = self.predict_proba(text)
        return max(probabilities, key=probabilities.get)

    def predict(self, texts):
        return [self.predict_one(text) for text in texts]

    def to_dict(self):
        return {
            "alpha": self.alpha,
            "labels": self.labels,
            "vocabulary": sorted(self.vocabulary),
            "class_doc_counts": dict(self.class_doc_counts),
            "class_token_counts": {
                label: dict(counter)
                for label, counter in self.class_token_counts.items()
            },
            "class_total_tokens": dict(self.class_total_tokens),
            "total_docs": self.total_docs,
        }

    @classmethod
    def from_dict(cls, data):
        model = cls(alpha=data["alpha"])
        model.labels = list(data["labels"])
        model.vocabulary = set(data["vocabulary"])
        model.class_doc_counts = Counter(data["class_doc_counts"])
        model.class_token_counts = defaultdict(Counter)
        for label, counts in data["class_token_counts"].items():
            model.class_token_counts[label] = Counter(counts)
        model.class_total_tokens = Counter(data["class_total_tokens"])
        model.total_docs = data["total_docs"]
        return model

    def save(self, path):
        with open(path, "w", encoding="utf-8") as file:
            json.dump(self.to_dict(), file, ensure_ascii=False, indent=2)

    @classmethod
    def load(cls, path):
        with open(path, "r", encoding="utf-8") as file:
            return cls.from_dict(json.load(file))


def accuracy_score(y_true, y_pred):
    if len(y_true) != len(y_pred):
        raise ValueError("y_true and y_pred must have the same length")
    if not y_true:
        return 0.0
    correct = sum(1 for actual, predicted in zip(y_true, y_pred) if actual == predicted)
    return correct / len(y_true)


def confusion_matrix(y_true, y_pred, labels):
    matrix = {actual: {predicted: 0 for predicted in labels} for actual in labels}
    for actual, predicted in zip(y_true, y_pred):
        matrix[actual][predicted] += 1
    return matrix


def classification_report(y_true, y_pred, labels):
    report = {}
    for label in labels:
        true_positive = sum(
            1 for actual, predicted in zip(y_true, y_pred)
            if actual == label and predicted == label
        )
        false_positive = sum(
            1 for actual, predicted in zip(y_true, y_pred)
            if actual != label and predicted == label
        )
        false_negative = sum(
            1 for actual, predicted in zip(y_true, y_pred)
            if actual == label and predicted != label
        )
        precision = (
            true_positive / (true_positive + false_positive)
            if true_positive + false_positive else 0.0
        )
        recall = (
            true_positive / (true_positive + false_negative)
            if true_positive + false_negative else 0.0
        )
        f1_score = (
            2 * precision * recall / (precision + recall)
            if precision + recall else 0.0
        )
        support = sum(1 for actual in y_true if actual == label)
        report[label] = {
            "precision": precision,
            "recall": recall,
            "f1_score": f1_score,
            "support": support,
        }
    return report

