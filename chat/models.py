import uuid

from django.conf import settings
from django.db import models


class Conversation(models.Model):
    """Una conversación. Pertenece a una sesión anónima y, opcionalmente, a un usuario."""

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL, null=True, blank=True,
        on_delete=models.SET_NULL, related_name="conversations",
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["-updated_at"]

    def __str__(self):
        return f"Conversación {self.id} ({self.created_at:%Y-%m-%d %H:%M})"


class Message(models.Model):
    class Role(models.TextChoices):
        USER = "user", "Usuario"
        BOT = "bot", "Bot"

    conversation = models.ForeignKey(Conversation, on_delete=models.CASCADE, related_name="messages")
    role = models.CharField(max_length=4, choices=Role.choices)
    content = models.TextField()
    # Metadatos del clasificador (solo en mensajes del bot): útiles para analítica y reentrenamiento
    intent = models.CharField(max_length=50, blank=True, default="")
    confidence = models.FloatField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["created_at", "id"]
        indexes = [models.Index(fields=["conversation", "created_at"])]

    def __str__(self):
        return f"[{self.role}] {self.content[:40]}"
