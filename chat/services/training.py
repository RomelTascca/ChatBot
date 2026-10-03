"""Entrenamiento del modelo (Secciones 4-7 del notebook): TF-IDF + LinearSVC con GridSearchCV."""
import json
import logging
from pathlib import Path

import joblib
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics import accuracy_score, classification_report
from sklearn.model_selection import GridSearchCV, train_test_split
from sklearn.pipeline import Pipeline
from sklearn.svm import LinearSVC

from .text_cleaner import STOP_WORDS, TextCleaner

logger = logging.getLogger(__name__)

MODEL_VERSION = "1.0"

FULL_GRID = {
    "tfidf__ngram_range": [(1, 1), (1, 2), (1, 3)],
    "tfidf__min_df": [1, 2, 3],
    "tfidf__max_df": [0.6, 0.7, 0.8, 1.0],
    "clf__C": [0.5, 1, 2, 4, 6, 8, 10, 12],
}

# Rejilla reducida para desarrollo y tests (segundos en lugar de ~1 min)
QUICK_GRID = {
    "tfidf__ngram_range": [(1, 1), (1, 2)],
    "tfidf__min_df": [1],
    "tfidf__max_df": [1.0],
    "clf__C": [1, 4],
}


def load_intents(intents_path: Path) -> dict:
    with open(intents_path, encoding="utf-8") as fh:
        return json.load(fh)


def build_samples(intents_data: dict) -> tuple[list[str], list[str]]:
    texts, labels = [], []
    for intent in intents_data["intents"]:
        for pattern in intent["patterns"]:
            texts.append(pattern.strip())
            labels.append(intent["tag"])
    return texts, labels


def train_and_save(intents_path: Path, model_path: Path, quick: bool = False, random_state: int = 42) -> dict:
    """Entrena, evalúa y guarda el modelo. Devuelve un resumen con métricas."""
    intents_data = load_intents(intents_path)
    X, y = build_samples(intents_data)

    X_train, X_test, y_train, y_test = train_test_split(
        X, y, test_size=0.25, random_state=random_state, stratify=y
    )

    pipeline = Pipeline([
        ("clean", TextCleaner()),
        ("tfidf", TfidfVectorizer(stop_words=STOP_WORDS)),
        ("clf", LinearSVC(class_weight="balanced")),
    ])

    grid = GridSearchCV(
        pipeline,
        param_grid=QUICK_GRID if quick else FULL_GRID,
        cv=3,
        n_jobs=-1,
    )
    grid.fit(X_train, y_train)
    best_model = grid.best_estimator_

    preds_test = best_model.predict(X_test)
    metrics = {
        "accuracy_train": accuracy_score(y_train, best_model.predict(X_train)),
        "accuracy_test": accuracy_score(y_test, preds_test),
        "best_params": grid.best_params_,
        "report": classification_report(y_test, preds_test, zero_division=0),
    }

    model_path = Path(model_path)
    model_path.parent.mkdir(parents=True, exist_ok=True)
    joblib.dump(
        {
            "version": MODEL_VERSION,
            "model": best_model,
            "intents": intents_data,
            "labels": sorted(set(y)),
        },
        model_path,
    )
    logger.info("Modelo guardado en %s (acc test=%.3f)", model_path, metrics["accuracy_test"])
    return metrics
