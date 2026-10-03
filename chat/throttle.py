"""Límite de peticiones simple por sesión/IP (ventana fija de 1 minuto, basado en la caché de Django)."""
from functools import wraps

from django.conf import settings
from django.core.cache import cache
from django.http import JsonResponse


def _client_id(request) -> str:
    # Garantiza una sesión: así la clave es la misma en la 1ª petición y en las siguientes
    if not request.session.session_key:
        request.session.create()
    return f"s:{request.session.session_key}"


def rate_limit(view):
    @wraps(view)
    def wrapper(request, *args, **kwargs):
        limit = settings.CHATBOT["RATE_LIMIT_PER_MINUTE"]
        if limit > 0:
            key = f"chat-rl:{_client_id(request)}"
            added = cache.add(key, 1, timeout=60)
            if not added:
                try:
                    count = cache.incr(key)
                except ValueError:  # expiró entre add e incr
                    cache.set(key, 1, timeout=60)
                    count = 1
                if count > limit:
                    return JsonResponse(
                        {"error": "Demasiadas solicitudes. Espera un momento e inténtalo de nuevo."},
                        status=429,
                    )
        return view(request, *args, **kwargs)

    return wrapper
