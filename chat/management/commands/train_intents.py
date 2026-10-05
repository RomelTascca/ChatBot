"""Entrena el clasificador TF-IDF + LinearSVC (secciones 4-7 del notebook)."""
import json

import joblib
from django.core.management.base import BaseCommand
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics import accuracy_score, classification_report
from sklearn.model_selection import GridSearchCV, train_test_split
from sklearn.pipeline import Pipeline
from sklearn.svm import LinearSVC

from chat.services.intent_classifier import INTENTS_PATH, MODEL_PATH
from chat.services.text_cleaner import STOP_WORDS, TextCleaner


class Command(BaseCommand):
    help = "Entrena el modelo de intenciones y lo guarda en chat/ml/intent_model.joblib"

    def add_arguments(self, parser):
        parser.add_argument("--fast", action="store_true", help="Grilla reducida (entrena en segundos).")

    def handle(self, *args, **options):
        data = json.loads(INTENTS_PATH.read_text(encoding="utf-8"))
        texts, labels = [], []
        for intent in data["intents"]:
            for pattern in intent["patterns"]:
                texts.append(pattern.strip())
                labels.append(intent["tag"])
        self.stdout.write(f"Dataset: {len(texts)} patrones, {len(set(labels))} intenciones")

        X_train, X_test, y_train, y_test = train_test_split(
            texts, labels, test_size=0.25, random_state=42, stratify=labels
        )

        pipeline = Pipeline([
            ("clean", TextCleaner()),
            ("tfidf", TfidfVectorizer(stop_words=STOP_WORDS)),
            ("clf", LinearSVC(class_weight="balanced")),
        ])

        if options["fast"]:
            grid = {"tfidf__ngram_range": [(1, 1), (1, 2)], "tfidf__min_df": [1], "clf__C": [1, 4, 10]}
        else:  # misma grilla del notebook
            grid = {
                "tfidf__ngram_range": [(1, 1), (1, 2), (1, 3)],
                "tfidf__min_df": [1, 2, 3],
                "tfidf__max_df": [0.6, 0.7, 0.8, 1.0],
                "clf__C": [0.5, 1, 2, 4, 6, 8, 10, 12],
            }

        search = GridSearchCV(pipeline, param_grid=grid, cv=3, n_jobs=-1)
        self.stdout.write("Entrenando (GridSearchCV)...")
        search.fit(X_train, y_train)
        best = search.best_estimator_

        preds = best.predict(X_test)
        self.stdout.write(f"Mejores hiperparámetros: {search.best_params_}")
        self.stdout.write(f"Accuracy entrenamiento: {accuracy_score(y_train, best.predict(X_train)):.4f}")
        self.stdout.write(f"Accuracy prueba:        {accuracy_score(y_test, preds):.4f}\n")
        self.stdout.write(classification_report(y_test, preds, zero_division=0))

        joblib.dump({"version": "1.0", "model": best, "labels": sorted(set(labels))}, MODEL_PATH)
        self.stdout.write(self.style.SUCCESS(f"Modelo guardado en {MODEL_PATH}"))
