"""Configuración de Django para el proyecto del chatbot."""
import os
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent


def env_bool(name: str, default: bool = False) -> bool:
    return os.environ.get(name, str(default)).strip().lower() in {"1", "true", "yes", "on"}


# --- Seguridad -------------------------------------------------------------
DEBUG = env_bool("DJANGO_DEBUG", True)
SECRET_KEY = os.environ.get("DJANGO_SECRET_KEY", "")
if not SECRET_KEY:
    if DEBUG:
        SECRET_KEY = "dev-only-insecure-key-change-me"
    else:
        raise RuntimeError("Define DJANGO_SECRET_KEY cuando DJANGO_DEBUG=False")

ALLOWED_HOSTS = [h.strip() for h in os.environ.get("DJANGO_ALLOWED_HOSTS", "localhost,127.0.0.1").split(",") if h.strip()]

# --- Apps ------------------------------------------------------------------
INSTALLED_APPS = [
    "django.contrib.admin",
    "django.contrib.auth",
    "django.contrib.contenttypes",
    "django.contrib.sessions",
    "django.contrib.messages",
    "django.contrib.staticfiles",
    "chat",
]

MIDDLEWARE = [
    "django.middleware.security.SecurityMiddleware",
    "django.contrib.sessions.middleware.SessionMiddleware",
    "django.middleware.common.CommonMiddleware",
    "django.middleware.csrf.CsrfViewMiddleware",
    "django.contrib.auth.middleware.AuthenticationMiddleware",
    "django.contrib.messages.middleware.MessageMiddleware",
    "django.middleware.clickjacking.XFrameOptionsMiddleware",
]

ROOT_URLCONF = "config.urls"

TEMPLATES = [
    {
        "BACKEND": "django.template.backends.django.DjangoTemplates",
        "DIRS": [],
        "APP_DIRS": True,
        "OPTIONS": {
            "context_processors": [
                "django.template.context_processors.request",
                "django.contrib.auth.context_processors.auth",
                "django.contrib.messages.context_processors.messages",
            ],
        },
    },
]

WSGI_APPLICATION = "config.wsgi.application"
ASGI_APPLICATION = "config.asgi.application"

# --- Base de datos ---------------------------------------------------------
DATABASES = {
    "default": {
        "ENGINE": "django.db.backends.sqlite3",
        "NAME": BASE_DIR / "db.sqlite3",
    }
}

AUTH_PASSWORD_VALIDATORS = [
    {"NAME": "django.contrib.auth.password_validation.UserAttributeSimilarityValidator"},
    {"NAME": "django.contrib.auth.password_validation.MinimumLengthValidator"},
    {"NAME": "django.contrib.auth.password_validation.CommonPasswordValidator"},
    {"NAME": "django.contrib.auth.password_validation.NumericPasswordValidator"},
]

# --- i18n ------------------------------------------------------------------
LANGUAGE_CODE = "es"
TIME_ZONE = "America/Lima"
USE_I18N = True
USE_TZ = True

# --- Estáticos -------------------------------------------------------------
STATIC_URL = "static/"
STATIC_ROOT = BASE_DIR / "staticfiles"

DEFAULT_AUTO_FIELD = "django.db.models.BigAutoField"

# --- Sesión y cookies --------------------------------------------------------
SESSION_COOKIE_AGE = 60 * 60 * 24 * 30  # 30 días: el historial del visitante anónimo vive lo mismo
SESSION_COOKIE_HTTPONLY = True
SESSION_COOKIE_SAMESITE = "Lax"
CSRF_COOKIE_SAMESITE = "Lax"

if not DEBUG:
    SECURE_SSL_REDIRECT = env_bool("DJANGO_SECURE_SSL_REDIRECT", True)
    SESSION_COOKIE_SECURE = True
    CSRF_COOKIE_SECURE = True
    SECURE_HSTS_SECONDS = 60 * 60 * 24 * 30
    SECURE_PROXY_SSL_HEADER = ("HTTP_X_FORWARDED_PROTO", "https")

# --- Chatbot -----------------------------------------------------------------
CHATBOT = {
    # Artefactos del modelo y dataset (reemplazan intents.json / intent_model.joblib del notebook)
    "INTENTS_PATH": BASE_DIR / "chat" / "ml" / "data" / "intents.json",
    "MODEL_PATH": BASE_DIR / "chat" / "ml" / "artifacts" / "intent_model.joblib",
    # Umbrales de decisión. El notebook usaba MIN_CONFIDENCE=0.15, pero esa métrica
    # (max|s|/sum|s|) nunca baja de 1/7, así que apenas filtra. Por defecto se usa el
    # MARGEN relativo entre las dos mejores clases (en el set de prueba: 78% -> ~94% de
    # acierto sobre lo que responde, derivando ~25% de consultas ambiguas a fallback).
    # Para replicar el notebook exacto: CONFIDENCE=0.15 y MARGIN=0.0.
    "MIN_CONFIDENCE": float(os.environ.get("CHATBOT_MIN_CONFIDENCE", "0.0")),
    "MIN_MARGIN": float(os.environ.get("CHATBOT_MIN_MARGIN", "0.10")),
    "FALLBACK_RESPONSES": [
        "No estoy seguro de lo que quieres decir. ¿Puedes reformularlo? "
        "Puedo ayudarte con horarios, precios, envíos, devoluciones o contacto.",
    ],
    "MAX_MESSAGE_LENGTH": 500,
    "HISTORY_LIMIT": 50,  # mensajes que se devuelven al frontend
    "RATE_LIMIT_PER_MINUTE": int(os.environ.get("CHATBOT_RATE_LIMIT_PER_MINUTE", "30")),
}

LOGGING = {
    "version": 1,
    "disable_existing_loggers": False,
    "formatters": {"simple": {"format": "%(asctime)s %(levelname)s %(name)s: %(message)s"}},
    "handlers": {"console": {"class": "logging.StreamHandler", "formatter": "simple"}},
    "loggers": {"chat": {"handlers": ["console"], "level": "INFO"}},
}
