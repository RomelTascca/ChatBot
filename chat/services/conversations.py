"""Gestión de la conversación asociada a la sesión de Django.

El id de la conversación vive en `request.session` (server-side), por lo que el
cliente nunca puede pedir la conversación de otro usuario manipulando un id.
"""
from ..models import Conversation

SESSION_KEY = "chat_conversation_id"


def get_or_create_conversation(request) -> Conversation:
    conversation = None
    conv_id = request.session.get(SESSION_KEY)
    if conv_id:
        conversation = Conversation.objects.filter(pk=conv_id).first()

    if conversation is None:
        conversation = Conversation.objects.create(
            user=request.user if request.user.is_authenticated else None
        )
        request.session[SESSION_KEY] = str(conversation.pk)
    elif request.user.is_authenticated and conversation.user_id is None:
        # El visitante inició sesión a mitad de conversación: la vinculamos a su cuenta
        conversation.user = request.user
        conversation.save(update_fields=["user", "updated_at"])

    return conversation


def reset_conversation(request) -> None:
    """Descarta la conversación actual (se conserva en BD) y empieza otra en la próxima petición."""
    request.session.pop(SESSION_KEY, None)
