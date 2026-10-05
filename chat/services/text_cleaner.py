"""Preprocesamiento de texto del notebook original (TextCleaner + STOP_WORDS)."""
import re
import unicodedata

from sklearn.base import BaseEstimator, TransformerMixin

STOP_WORDS = [
    "el", "la", "los", "las", "de", "del", "un", "una", "unos", "unas",
    "y", "en", "para", "por", "con", "que", "a", "al", "lo", "es", "son",
    "me", "mi", "mis", "tu", "tus", "su", "sus",
]


class TextCleaner(BaseEstimator, TransformerMixin):
    """Minúsculas, sin tildes, sin URLs ni números, sin símbolos."""

    def fit(self, X, y=None):
        return self

    def transform(self, X):
        cleaned = []
        for text in X:
            text = text.lower()
            text = unicodedata.normalize("NFKD", text)
            text = "".join(c for c in text if not unicodedata.combining(c))
            text = re.sub(r"http\S+|www\.\S+", " ", text)
            text = re.sub(r"\d+", " ", text)
            text = re.sub(r"[^a-z0-9\s]", " ", text)
            text = re.sub(r"\s+", " ", text).strip()
            cleaned.append(text)
        return cleaned
