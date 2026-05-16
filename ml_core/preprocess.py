"""Text preprocessing helpers implemented with the Python standard library."""

import re
from collections import Counter


TOKEN_PATTERN = re.compile(r"[0-9A-Za-z\u00C0-\u1EF9]+", re.UNICODE)

STOP_WORDS = {
    "and",
    "are",
    "as",
    "be",
    "by",
    "for",
    "from",
    "in",
    "is",
    "la",
    "of",
    "on",
    "or",
    "the",
    "to",
    "with",
    "bị",
    "bằng",
    "các",
    "cái",
    "cho",
    "có",
    "của",
    "để",
    "được",
    "giúp",
    "hay",
    "hoặc",
    "khi",
    "là",
    "một",
    "này",
    "như",
    "những",
    "nhiều",
    "theo",
    "thì",
    "trong",
    "và",
    "vào",
    "với",
}


def tokenize(text):
    """Normalize text and return meaningful tokens."""
    if not text:
        return []

    tokens = TOKEN_PATTERN.findall(text.lower())
    return [token for token in tokens if token not in STOP_WORDS and len(token) > 1]


def build_features(text):
    """Return unigram and bigram features for text classification."""
    tokens = tokenize(text)
    bigrams = [
        f"{tokens[index]}_{tokens[index + 1]}"
        for index in range(len(tokens) - 1)
    ]
    return tokens + bigrams


def count_tokens(text):
    """Return a token frequency counter for a text sample."""
    return Counter(build_features(text))
