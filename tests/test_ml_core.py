import unittest

from ml_core.knn import KNearestNeighborClassifier
from ml_core.naive_bayes import MultinomialNaiveBayes, accuracy_score
from ml_core.preprocess import count_tokens, tokenize


class TestPreprocess(unittest.TestCase):
    def test_tokenize_removes_stop_words_and_lowercases(self):
        tokens = tokenize("Python la NGON NGU lap trinh.")

        self.assertIn("python", tokens)
        self.assertIn("ngon", tokens)
        self.assertNotIn("la", tokens)

    def test_count_tokens_includes_bigrams(self):
        token_counts = count_tokens("linear regression model")

        self.assertEqual(token_counts["linear"], 1)
        self.assertEqual(token_counts["linear_regression"], 1)
        self.assertEqual(token_counts["regression_model"], 1)


class TestMultinomialNaiveBayes(unittest.TestCase):
    def test_predicts_topic_from_simple_training_data(self):
        texts = [
            "python list dictionary function",
            "python class object method",
            "database sql table query",
            "database primary key foreign key",
        ]
        labels = ["python", "python", "database", "database"]

        model = MultinomialNaiveBayes()
        model.fit(texts, labels)

        self.assertEqual(model.predict_one("sql query table"), "database")
        self.assertEqual(model.predict_one("python function class"), "python")

    def test_accuracy_score(self):
        self.assertEqual(accuracy_score(["a", "b", "b"], ["a", "a", "b"]), 2 / 3)


class TestKNearestNeighborClassifier(unittest.TestCase):
    def test_predicts_topic_from_nearest_neighbors(self):
        texts = [
            "python list dictionary function",
            "python class object method",
            "database sql table query",
            "database primary key foreign key",
        ]
        labels = ["python", "python", "database", "database"]

        model = KNearestNeighborClassifier(k=1)
        model.fit(texts, labels)

        self.assertEqual(model.predict_one("sql query table"), "database")
        self.assertEqual(model.predict_one("python function class"), "python")

    def test_predict_proba_sums_to_one(self):
        model = KNearestNeighborClassifier(k=2)
        model.fit(["python function", "sql database"], ["python", "database"])

        probabilities = model.predict_proba("python")

        self.assertAlmostEqual(sum(probabilities.values()), 1.0)


if __name__ == "__main__":
    unittest.main()
