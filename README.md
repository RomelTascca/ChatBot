# Chatbot de intenciones (TF-IDF + SVM) con Django 5.2

## Puesta en marcha

```bash
python -m venv .venv && source .venv/bin/activate      # Windows: .venv\Scripts\activate
pip install -r requirements.txt
#cp .env.example .env                                   # opcional; exporta las variables o usa un gestor de .env
python manage.py migrate
python manage.py train_chatbot                         # genera chat/ml/artifacts/intent_model.joblib (usa --quick en desarrollo)
#python manage.py createsuperuser                       # opcional, para ver el historial en /admin
python manage.py runserver
```

Abre http://127.0.0.1:8000/

## Tests
```bash
python manage.py test chat # Correr este comando para realizar pruebas del chat
```

## Estructura

| Ruta | Rol |
|---|---|
| `config/` | Settings, URLs raíz, WSGI/ASGI |
| `chat/services/text_cleaner.py` | `TextCleaner` + stop words (notebook §3) |
| `chat/services/training.py` | Pipeline TF-IDF + LinearSVC + GridSearchCV (§4-7) |
| `chat/services/intent_classifier.py` | Predicción + confianza + margen (§8) |
| `chat/services/chatbot.py` | Orquestador: valida, clasifica, memoria, persistencia |
| `chat/services/conversations.py` | Conversación ligada a la sesión de Django |
| `chat/models.py` | `Conversation`, `Message` |
| `chat/views.py`, `chat/urls.py` | Endpoints JSON + página del chat |
| `chat/management/commands/train_chatbot.py` | `python manage.py train_chatbot` |
| `chat/ml/data/intents.json` | Dataset extraído del notebook (7 intenciones, 251 patrones) |
| `chat/templates/`, `chat/static/` | Frontend (HTML, CSS, JS con fetch) |

## API

| Método | Ruta | Descripción |
|---|---|---|
| GET | `/` | Página del chat (con historial incrustado) |
| POST | `/api/chat/` | `{"message": "..."}` → `{"reply","intent","confidence"}` |
| GET | `/api/history/` | Historial de la conversación actual |
| POST | `/api/reset/` | Empieza una conversación nueva |

Los POST requieren cabecera `X-CSRFToken`.
