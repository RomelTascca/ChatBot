"""Predicción de intención + confianza (Sección 8 del notebook).

Lógica equivalente a `compute_confidence` y `predict_intent` del notebook,
pero cargando el modelo una sola vez (singleton thread-safe) en lugar de
hacerlo en cada petición.
"""
import logging
import threading
from dataclasses import dataclass, field
from pathlib import Path

import joblib
import numpy as np

from .exceptions import ModelNotTrainedError

logger = logging.getLogger(__name__)


@dataclass(frozen=True)
class Prediction:
    intent: str | None          # None = no se entendió (fallback)
    confidence: float
    margin: float               # margen relativo entre la 1ª y 2ª clase
    responses: list[str] = field(default_factory=list)


def compute_confidence(scores: np.ndarray) -> float:
    """Misma fórmula del notebook: max(|s|) / sum(|s|).

    OJO: con N clases el mínimo posible es 1/N (aquí 1/7 ≈ 0.143), así que un
    umbral de 0.15 casi nunca descarta nada. Ver `margin` y las recomendaciones.
    """
    sum_abs = float(np.sum(np.abs(scores)))
    if sum_abs == 0:
        return 0.0
    return float(np.max(np.abs(scores)) / sum_abs)


def compute_margin(scores: np.ndarray) -> float:
    """Margen relativo: (mejor - segunda mejor) / sum(|s|).

    Es invariante a la escala de los scores, así que el umbral sigue siendo válido
    aunque GridSearchCV elija otro `C` al reentrenar. Ruido/sinsentidos ≈ 0.005;
    consultas claras ≥ 0.10. (0 = empate total entre las dos mejores clases.)
    """
    if scores.size < 2:
        return 1.0
    sum_abs = float(np.sum(np.abs(scores)))
    if sum_abs == 0:
        return 0.0
    top2 = np.sort(scores)[-2:]
    return float((top2[1] - top2[0]) / sum_abs)


class IntentClassifier:
    def __init__(self, model_path: Path, min_confidence: float = 0.0, min_margin: float = 0.10,
                 fallback_responses: list[str] | None = None):
        self.model_path = Path(model_path)
        self.min_confidence = min_confidence
        self.min_margin = min_margin
        self.fallback_responses = fallback_responses or ["No estoy seguro de lo que quieres decir. ¿Puedes reformularlo?"]
        self._pack = None
        self._lock = threading.Lock()

    # -- carga perezosa ---------------------------------------------------
    def _load(self) -> dict:
        if self._pack is None:
            with self._lock:
                if self._pack is None:
                    if not self.model_path.exists():
                        raise ModelNotTrainedError(
                            f"No existe {self.model_path}. Ejecuta: python manage.py train_chatbot"
                        )
                    self._pack = joblib.load(self.model_path)
                    logger.info("Modelo cargado (versión %s)", self._pack.get("version"))
        return self._pack

    def reload(self) -> None:
        with self._lock:
            self._pack = None

    # -- API pública --------------------------------------------------------
    def predict(self, text: str) -> Prediction:
        pack = self._load()
        model = pack["model"]

        scores = np.asarray(model.decision_function([text])[0], dtype=float)
        confidence = compute_confidence(scores)
        margin = compute_margin(scores)

        if confidence < self.min_confidence or margin < self.min_margin:
            return Prediction(None, confidence, margin, list(self.fallback_responses))

        label = model.classes_[int(np.argmax(scores))]
        for intent in pack["intents"]["intents"]:
            if intent["tag"] == label:
                return Prediction(label, confidence, margin, list(intent["responses"]))

        return Prediction(None, confidence, margin, ["No entendí bien tu consulta."])
