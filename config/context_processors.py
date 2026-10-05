from django.conf import settings


def store_info(request):
    """Expone datos de la tienda a todas las plantillas."""
    return {
        "STORE_NAME": settings.STORE_NAME,
        "STORE_WHATSAPP": settings.STORE_WHATSAPP,
        "STORE_HOURS": settings.STORE_HOURS,
    }
