import uuid

from django.conf import settings
from django.db import models


class Conversation(models.Model):
    """Una conversación = un hilo de chat, ligado a una sesión (y a un usuario si está logueado)."""

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    session_key = models.CharField(max_length=40, db_index=True)
    user = models.ForeignKey(settings.AUTH_USER_MODEL, null=True, blank=True, on_delete=models.SET_NULL,
                             related_name="conversations")
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["-updated_at"]

    def __str__(self):
        return f"Conversación {str(self.id)[:8]}"

    def recent_messages(self, limit: int):
        """Los últimos `limit` mensajes en orden cronológico."""
        latest = list(self.messages.order_by("-id")[:limit])
        return latest[::-1]


class Message(models.Model):
    class Role(models.TextChoices):
        USER = "user", "Usuario"
        ASSISTANT = "assistant", "Asistente"

    class Source(models.TextChoices):
        GEMINI = "gemini", "Gemini"
        SHORTCUT = "shortcut", "Clasificador ML (sin Gemini)"
        FALLBACK = "fallback", "Respuesta de respaldo"

    conversation = models.ForeignKey(Conversation, on_delete=models.CASCADE, related_name="messages")
    role = models.CharField(max_length=10, choices=Role.choices)
    content = models.TextField()
    intent = models.CharField(max_length=40, blank=True)
    confidence = models.FloatField(null=True, blank=True)
    source = models.CharField(max_length=10, choices=Source.choices, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["id"]

    def __str__(self):
        return f"[{self.role}] {self.content[:50]}"
