import json
import logging

from django.conf import settings
from django.core.cache import cache
from django.http import JsonResponse
from django.shortcuts import render
from django.views.decorators.http import require_GET, require_POST

from .models import Conversation, Message
from .services.chatbot import get_chatbot_service

logger = logging.getLogger(__name__)

SESSION_KEY = "chat_conversation_id"

SUGGESTIONS = [
    "¿Qué zapatillas tienen?",
    "¿Cuánto cuesta el envío a provincia?",
    "¿Cómo hago un cambio de talla?",
    "¿Qué métodos de pago aceptan?",
]


# ----------------------------------------------------------------- helpers
def _ensure_session(request) -> str:
    if not request.session.session_key:
        request.session.save()
    return request.session.session_key


def _get_conversation(request, create: bool) -> Conversation | None:
    session_key = _ensure_session(request)
    conv_id = request.session.get(SESSION_KEY)
    if conv_id:
        conversation = Conversation.objects.filter(id=conv_id, session_key=session_key).first()
        if conversation:
            return conversation
    if not create:
        return None
    conversation = Conversation.objects.create(
        session_key=session_key,
        user=request.user if request.user.is_authenticated else None,
    )
    request.session[SESSION_KEY] = str(conversation.id)
    return conversation


def _rate_limited(request) -> bool:
    key = f"chat:rl:{_ensure_session(request)}"
    cache.add(key, 0, 60)
    try:
        return cache.incr(key) > settings.CHAT_RATE_LIMIT_PER_MINUTE
    except ValueError:  # la clave expiró entre add() e incr()
        cache.set(key, 1, 60)
        return False


def _serialize(message: Message) -> dict:
    return {"role": message.role, "content": message.content, "source": message.source}


# ------------------------------------------------------------------- views
@require_GET
def chat_page(request):
    conversation = _get_conversation(request, create=False)
    messages = [_serialize(m) for m in conversation.messages.all()] if conversation else []
    return render(request, "chat/chat.html", {"initial_messages": messages, "suggestions": SUGGESTIONS})


@require_POST
def send_message(request):
    try:
        payload = json.loads(request.body or b"{}")
    except json.JSONDecodeError:
        return JsonResponse({"error": "JSON inválido."}, status=400)

    text = str(payload.get("message", "")).strip()
    if not text:
        return JsonResponse({"error": "Escribe un mensaje."}, status=400)
    if len(text) > settings.CHAT_MAX_MESSAGE_CHARS:
        return JsonResponse(
            {"error": f"El mensaje supera los {settings.CHAT_MAX_MESSAGE_CHARS} caracteres."}, status=400
        )
    if _rate_limited(request):
        return JsonResponse({"error": "Demasiados mensajes. Espera un momento e inténtalo otra vez."}, status=429)

    conversation = _get_conversation(request, create=True)
    history = [{"role": m.role, "content": m.content}
               for m in conversation.recent_messages(settings.CHAT_HISTORY_TURNS)]

    Message.objects.create(conversation=conversation, role=Message.Role.USER, content=text)
    reply = get_chatbot_service().reply(text, history)
    Message.objects.create(
        conversation=conversation, role=Message.Role.ASSISTANT, content=reply.text,
        intent=reply.intent, confidence=reply.confidence, source=reply.source,
    )
    conversation.save(update_fields=["updated_at"])

    return JsonResponse({"reply": reply.text, "source": reply.source, "intent": reply.intent})


@require_POST
def reset_conversation(request):
    request.session.pop(SESSION_KEY, None)
    return JsonResponse({"ok": True})
