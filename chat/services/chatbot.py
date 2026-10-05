"""
Servicio del chatbot: orquesta clasificador ML (notebook) + Gemini.

Flujo de `ChatbotService.reply()`:
  1. El clasificador TF-IDF + SVM detecta la intención del mensaje.
  2. Saludos/despedidas cortos -> respuesta inmediata (sin gastar una llamada a Gemini).
  3. Todo lo demás -> Gemini (gemini-3.8-flash) con el catálogo real en la instrucción de sistema.
  4. Si Gemini falla (sin clave, timeout, cuota...) -> respuesta de respaldo amable. Nunca rompe la web.
"""
import logging
from dataclasses import dataclass

from django.conf import settings
from google import genai

from .intent_classifier import IntentResult, intent_classifier
from .prompt_builder import build_system_prompt

logger = logging.getLogger(__name__)

SHORTCUT_INTENTS = {"saludo", "despedida"}
SHORTCUT_MAX_WORDS = 4


class GeminiNotConfigured(RuntimeError):
    """Falta GEMINI_API_KEY en el .env."""


@dataclass
class BotReply:
    text: str
    source: str                      # "gemini" | "shortcut" | "fallback"
    intent: str = ""
    confidence: float | None = None


class ChatbotService:
    def __init__(self):
        self._client = None

    # ------------------------------------------------------------------
    # >>> AQUÍ SE USA LA API KEY <<<
    # settings.GEMINI_API_KEY se lee del archivo .env (variable GEMINI_API_KEY)
    # en config/settings.py y se pasa al cliente con `api_key=`.
    # ------------------------------------------------------------------
    def _get_client(self) -> genai.Client:
        if self._client is None:
            api_key = settings.GEMINI_API_KEY
            if not api_key or api_key.startswith("pega_aqui"):
                raise GeminiNotConfigured("GEMINI_API_KEY no está configurada en el archivo .env")
            self._client = genai.Client(api_key=api_key)
        return self._client

    # ------------------------------------------------------------------
    def reply(self, user_text: str, history: list[dict]) -> BotReply:
        """
        user_text: mensaje actual del cliente.
        history:   mensajes previos [{"role": "user"|"assistant", "content": str}, ...].
        """
        intent = intent_classifier.predict(user_text)
        intent_tag = intent.tag if intent else ""
        confidence = intent.confidence if intent else None

        shortcut = self._try_shortcut(user_text, intent)
        if shortcut:
            return BotReply(shortcut, "shortcut", intent_tag, confidence)

        try:
            text = self._call_gemini(user_text, history, intent)
            if text:
                return BotReply(text, "gemini", intent_tag, confidence)
            logger.warning("Gemini devolvió una respuesta vacía")
        except GeminiNotConfigured as exc:
            logger.error("%s", exc)
        except Exception as exc:  # errores de red, cuota, clave inválida, etc.
            status = getattr(exc, "status_code", None)
            # Se registra solo el mensaje y el código HTTP (nunca la clave ni los headers).
            logger.error("Error llamando a Gemini (HTTP %s): %s", status, exc)

        return BotReply(self._fallback_text(), "fallback", intent_tag, confidence)

    # ------------------------------------------------------------------
    def _try_shortcut(self, user_text: str, intent: IntentResult | None) -> str | None:
        if intent is None or intent.tag not in SHORTCUT_INTENTS:
            return None
        if intent.margin < settings.CHAT_INTENT_MIN_MARGIN:   # mensajes mixtos tienen margen bajo
            return None
        if len(user_text.split()) > SHORTCUT_MAX_WORDS:   # "hola, ¿cuánto cuesta el polo?" -> Gemini
            return None
        return intent_classifier.canned_response(intent.tag)

    def _call_gemini(self, user_text: str, history: list[dict], intent: IntentResult | None) -> str:
        client = self._get_client()

        # Historial en formato "stateless" de la Interactions API (se guarda en NUESTRA base de datos).
        steps = []
        for item in history:
            step_type = "user_input" if item["role"] == "user" else "model_output"
            steps.append({"type": step_type, "content": [{"type": "text", "text": item["content"]}]})
        while steps and steps[0]["type"] != "user_input":   # el hilo debe empezar con el usuario
            steps.pop(0)
        steps.append({"type": "user_input", "content": [{"type": "text", "text": user_text}]})

        kwargs = {
            "model": settings.GEMINI_MODEL,                 # "gemini-3.8-flash"
            "input": steps,
            "system_instruction": build_system_prompt(intent),
            "store": False,                                  # no se guarda la conversación en los servidores de Google
            "timeout": settings.GEMINI_TIMEOUT_SECONDS,
        }
        if settings.GEMINI_THINKING_LEVEL:
            kwargs["generation_config"] = {"thinking_level": settings.GEMINI_THINKING_LEVEL}

        interaction = client.interactions.create(**kwargs)
        return (interaction.output_text or "").strip()

    @staticmethod
    def _fallback_text() -> str:
        return (
            "Ahora mismo no puedo responder tu consulta 😕. Por favor inténtalo de nuevo en unos minutos "
            f"o escríbenos por WhatsApp al {settings.STORE_WHATSAPP} ({settings.STORE_HOURS})."
        )


_service: ChatbotService | None = None


def get_chatbot_service() -> ChatbotService:
    global _service
    if _service is None:
        _service = ChatbotService()
    return _service
