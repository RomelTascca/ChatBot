"""Orquestador del chatbot: valida, clasifica, usa la memoria y persiste.

Es la única pieza que conoce a la vez el clasificador y los modelos de Django;
las vistas solo llaman a `ChatbotService.reply(...)`.

Sobre la "memoria": el clasificador TF-IDF + SVM es *stateless* (cada mensaje se
clasifica solo). La memoria se usa para (1) persistir y mostrar el historial y
(2) no repetir la misma respuesta dos veces seguidas. Si algún día se conecta un
LLM, `recent_history()` ya entrega el contexto en el formato necesario.
"""
import random
from dataclasses import dataclass

from django.conf import settings
from django.db import transaction

from ..models import Conversation, Message
from .exceptions import InvalidMessageError
from .intent_classifier import IntentClassifier


@dataclass(frozen=True)
class BotReply:
    text: str
    intent: str | None
    confidence: float


def build_default_classifier() -> IntentClassifier:
    cfg = settings.CHATBOT
    return IntentClassifier(
        model_path=cfg["MODEL_PATH"],
        min_confidence=cfg["MIN_CONFIDENCE"],
        min_margin=cfg["MIN_MARGIN"],
        fallback_responses=cfg["FALLBACK_RESPONSES"],
    )


# Instancia compartida por proceso (el modelo se carga una sola vez)
_classifier: IntentClassifier | None = None


def get_classifier() -> IntentClassifier:
    global _classifier
    if _classifier is None:
        _classifier = build_default_classifier()
    return _classifier


def set_classifier(classifier: IntentClassifier | None) -> None:
    """Permite inyectar/reiniciar el clasificador (tests, recarga tras reentrenar)."""
    global _classifier
    _classifier = classifier


class ChatbotService:
    def __init__(self, classifier: IntentClassifier | None = None):
        self.classifier = classifier or get_classifier()
        self.max_length = settings.CHATBOT["MAX_MESSAGE_LENGTH"]

    # -- validación ---------------------------------------------------------
    def validate(self, text) -> str:
        if not isinstance(text, str):
            raise InvalidMessageError("El mensaje debe ser texto.")
        text = text.strip()
        if not text:
            raise InvalidMessageError("Por favor, escribe un mensaje.")
        if len(text) > self.max_length:
            raise InvalidMessageError(f"El mensaje no puede superar {self.max_length} caracteres.")
        return text

    # -- memoria ------------------------------------------------------------
    @staticmethod
    def recent_history(conversation: Conversation, limit: int = 10) -> list[dict]:
        """Últimos mensajes en formato {role, content} (útil si se conecta un LLM)."""
        qs = conversation.messages.order_by("-created_at", "-id")[:limit]
        return [{"role": m.role, "content": m.content} for m in reversed(list(qs))]

    @staticmethod
    def _last_bot_text(conversation: Conversation) -> str | None:
        last = conversation.messages.filter(role=Message.Role.BOT).order_by("-created_at", "-id").first()
        return last.content if last else None

    # -- flujo principal ------------------------------------------------------
    def reply(self, conversation: Conversation, user_text: str) -> BotReply:
        text = self.validate(user_text)

        # Clasificar primero: si el modelo falla no dejamos mensajes huérfanos en BD
        prediction = self.classifier.predict(text)

        last_bot = self._last_bot_text(conversation)
        candidates = [r for r in prediction.responses if r != last_bot] or prediction.responses
        answer = random.choice(candidates)

        with transaction.atomic():
            Message.objects.create(conversation=conversation, role=Message.Role.USER, content=text)
            Message.objects.create(
                conversation=conversation,
                role=Message.Role.BOT,
                content=answer,
                intent=prediction.intent or "",
                confidence=prediction.confidence,
            )
            conversation.save(update_fields=["updated_at"])

        return BotReply(text=answer, intent=prediction.intent, confidence=prediction.confidence)
