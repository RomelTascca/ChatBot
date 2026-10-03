class ChatbotError(Exception):
    """Error base del dominio del chatbot."""


class ModelNotTrainedError(ChatbotError):
    """No existe el artefacto del modelo. Ejecuta `python manage.py train_chatbot`."""


class InvalidMessageError(ChatbotError):
    """El mensaje del usuario no es válido (vacío o demasiado largo)."""
