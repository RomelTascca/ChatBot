import json
import logging

from django.conf import settings
from django.http import JsonResponse
from django.shortcuts import render
from django.views.decorators.http import require_GET, require_POST

from .models import Message
from .services.chatbot import ChatbotService
from .services.conversations import get_or_create_conversation, reset_conversation
from .services.exceptions import InvalidMessageError, ModelNotTrainedError
from .throttle import rate_limit

logger = logging.getLogger(__name__)


def _serialize(message: Message) -> dict:
    return {
        "role": message.role,
        "content": message.content,
        "intent": message.intent or None,
        "created_at": message.created_at.isoformat(),
    }


def _history(conversation) -> list[dict]:
    limit = settings.CHATBOT["HISTORY_LIMIT"]
    recent = conversation.messages.order_by("-created_at", "-id")[:limit]
    return [_serialize(m) for m in reversed(list(recent))]


@require_GET
def index(request):
    """Página del chat. El historial inicial se incrusta en el HTML (sin petición extra)."""
    conversation = get_or_create_conversation(request)
    return render(request, "chat/index.html", {
        "history": _history(conversation),
        "max_length": settings.CHATBOT["MAX_MESSAGE_LENGTH"],
    })


@require_POST
@rate_limit
def send_message(request):
    """POST /api/chat/  {"message": "..."}  ->  {"reply": "...", "intent": "...", "confidence": 0.42}"""
    try:
        payload = json.loads(request.body or b"{}")
    except json.JSONDecodeError:
        return JsonResponse({"error": "JSON inválido."}, status=400)

    if not isinstance(payload, dict):
        return JsonResponse({"error": "Formato de solicitud inválido."}, status=400)

    conversation = get_or_create_conversation(request)

    try:
        reply = ChatbotService().reply(conversation, payload.get("message"))
    except InvalidMessageError as exc:
        return JsonResponse({"error": str(exc)}, status=400)
    except ModelNotTrainedError:
        logger.error("Modelo no entrenado. Ejecuta: python manage.py train_chatbot")
        return JsonResponse({"error": "El asistente no está disponible por el momento."}, status=503)
    except Exception:
        logger.exception("Error inesperado procesando el mensaje")
        return JsonResponse({"error": "Ocurrió un error inesperado. Inténtalo de nuevo."}, status=500)

    return JsonResponse({
        "reply": reply.text,
        "intent": reply.intent,
        "confidence": round(reply.confidence, 3),
    })


@require_GET
def history(request):
    conversation = get_or_create_conversation(request)
    return JsonResponse({"messages": _history(conversation)})


@require_POST
def reset(request):
    reset_conversation(request)
    return JsonResponse({"ok": True})
