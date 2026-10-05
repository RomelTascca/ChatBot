"""
Clasificador de intenciones (TF-IDF + LinearSVC) — lógica `predict_intent` del notebook.

Funciona como "primera capa" del chatbot:
  * detecta la intención (saludo, precios, envio...) y se la pasa a Gemini como pista;
  * responde directamente (sin gastar una llamada a Gemini) solo en saludos/despedidas simples.

Si el modelo aún no fue entrenado (`python manage.py train_intents`), el chatbot sigue
funcionando solo con Gemini.
"""
import json
import logging
import random
import threading
from dataclasses import dataclass
from pathlib import Path

import joblib
import numpy as np

from .text_cleaner import TextCleaner  # noqa: F401  (necesario para deserializar el modelo)

logger = logging.getLogger(__name__)

ML_DIR = Path(__file__).resolve().parent.parent / "ml"
MODEL_PATH = ML_DIR / "intent_model.joblib"
INTENTS_PATH = ML_DIR / "intents.json"


@dataclass(frozen=True)
class IntentResult:
    tag: str
    confidence: float      # métrica del notebook (max|s| / sum|s|): se registra, pero discrimina poco con 7 clases
    margin: float = 0.0    # distancia entre la 1ª y la 2ª clase: la usamos para decidir (>= ~1.5 = muy seguro)


def compute_confidence(model, text: str) -> float:
    """Misma fórmula del notebook: max|score| / sum|scores| de decision_function."""
    try:
        scores = model.decision_function([text])
    except Exception:
        return 1.0
    scores_arr = np.array(scores[0] if hasattr(scores[0], "__len__") else scores, dtype=float)
    total = float(np.sum(np.abs(scores_arr)))
    if total == 0:
        return 0.0
    return float(np.max(np.abs(scores_arr)) / total)


def compute_margin(model, text: str) -> float:
    """Diferencia entre el mejor y el segundo mejor score de decision_function."""
    try:
        scores = np.sort(np.array(model.decision_function([text])[0], dtype=float))[::-1]
        return float(scores[0] - scores[1])
    except Exception:
        return 0.0


class IntentClassifier:
    def __init__(self, model_path: Path = MODEL_PATH, intents_path: Path = INTENTS_PATH):
        self.model_path = model_path
        self.intents_path = intents_path
        self._model = None
        self._responses: dict[str, list[str]] = {}
        self._loaded = False
        self._lock = threading.Lock()

    def _load(self) -> bool:
        if self._loaded:
            return self._model is not None
        with self._lock:
            if self._loaded:
                return self._model is not None
            try:
                pack = joblib.load(self.model_path)  # archivo propio generado por train_intents
                self._model = pack["model"]
                intents = json.loads(self.intents_path.read_text(encoding="utf-8"))["intents"]
                self._responses = {item["tag"]: item["responses"] for item in intents}
            except FileNotFoundError:
                logger.warning("Modelo de intenciones no encontrado. Ejecuta: python manage.py train_intents")
            except Exception:
                logger.exception("No se pudo cargar el modelo de intenciones")
            self._loaded = True
            return self._model is not None

    def reload(self) -> None:
        self._loaded = False
        self._model = None

    def predict(self, text: str) -> IntentResult | None:
        if not self._load():
            return None
        try:
            tag = self._model.predict([text])[0]
            return IntentResult(
                tag=str(tag),
                confidence=compute_confidence(self._model, text),
                margin=compute_margin(self._model, text),
            )
        except Exception:
            logger.exception("Falló la predicción de intención")
            return None

    def canned_response(self, tag: str) -> str | None:
        options = self._responses.get(tag)
        return random.choice(options) if options else None


intent_classifier = IntentClassifier()
