# 🤖 Chatbot

## 1. Estructura del proyecto

```
django_gemini_chatbot/
├── .env.example            ← plantilla de variables (cópiala a .env)
├── .gitignore              ← ya excluye .env, db.sqlite3 y el modelo .joblib
├── manage.py
├── requirements.txt
├── config/                 ← configuración del proyecto
│   ├── settings.py         ← AQUÍ se carga el .env y se lee GEMINI_API_KEY
│   ├── urls.py
│   └── context_processors.py
├── catalog/                ← app de productos y servicios
│   ├── models.py           ← Category, Product, Offering
│   ├── views.py · urls.py · admin.py
│   ├── seed_data.py        ← 12 productos + 13 servicios/beneficios
│   ├── management/commands/seed_data.py
│   └── templates/catalog/  ← product_list.html, offering_list.html
├── chat/                   ← app del chatbot
│   ├── models.py           ← Conversation, Message (historial)
│   ├── views.py · urls.py · admin.py
│   ├── services/           ← LÓGICA DE NEGOCIO (sin nada de HTTP)
│   │   ├── chatbot.py          ← orquestador + llamada a Gemini  ⭐
│   │   ├── prompt_builder.py   ← arma el prompt con el catálogo
│   │   ├── intent_classifier.py← clasificador del notebook
│   │   └── text_cleaner.py     ← TextCleaner + STOP_WORDS del notebook
│   ├── ml/intents.json     ← dataset original (7 intenciones, 251 patrones)
│   ├── management/commands/train_intents.py
│   └── templates/chat/chat.html
├── templates/base.html
└── static/
    ├── css/app.css
    └── js/chat.js          ← frontend del chat
```

---

## 2. Instalación paso a paso

> Requiere Python 3.10+ (probado con 3.12).

```bash
# 1) Entrar a la carpeta y crear el entorno virtual
cd django_gemini_chatbot
python -m venv venv
source venv/bin/activate            # Windows: venv\Scripts\activate

# 2) Instalar dependencias (Django, google-genai, python-dotenv, scikit-learn...)
pip install -r requirements.txt

# 3) Crear tu archivo .env a partir de la plantilla
cp .env.example .env                # Windows: copy .env.example .env

# 4) >>> Editar .env y pegar tu API key (ver sección 3) <<<

# 5) Crear la base de datos
python manage.py migrate

# 6) Cargar los 12 productos y los 13 servicios/beneficios de ejemplo
python manage.py seed_data

# 7) Entrenar el clasificador de intenciones del notebook
python manage.py train_intents          # grilla completa del notebook (~1-2 min)
# python manage.py train_intents --fast # versión rápida (segundos)

# 8) (Opcional) crear un administrador para ver conversaciones en /admin
python manage.py createsuperuser

# 9) Ejecutar
python manage.py runserver
```

Abre **http://127.0.0.1:8000/** (chat) · `/productos/` · `/servicios/` · `/admin/`.

> Si omites el paso 7 el chatbot funciona igual, solo con Gemini (verás un aviso en la consola).

---

## 4. Cómo funciona una conversación

```
Navegador (chat.js) ──POST /chat/api/send/──► views.send_message
                                                │ valida, rate-limit, guarda mensaje
                                                ▼
                                    services/chatbot.ChatbotService.reply()
                                                │
                    ┌───────────────────────────┴────────────────────────┐
                    ▼                                                    ▼
      Clasificador ML (saludo/despedida corto,           Gemini 3.8 Flash + catálogo real
      margen alto) → respuesta inmediata                 (historial desde NUESTRA base de datos)
                    └───────────────► guarda respuesta ◄──────────────────┘
```

- **Historial por sesión:** cada visitante tiene una `Conversation` ligada a su sesión (y a su usuario si
  está logueado). Se envían a Gemini los últimos `CHAT_HISTORY_TURNS` (10) mensajes.
- **Privacidad:** se llama con `store=False`; Google no conserva el hilo, el historial vive solo en tu BD.
- **Botón "Nueva conversación"** abre un hilo nuevo.
- En `/admin/` puedes revisar cada conversación, la intención detectada y si respondió Gemini, el
  clasificador o el respaldo.

### Sobre la "confianza" del notebook
Con 7 clases, la métrica `max|score| / sum|scores|` del notebook queda en ≈0.15–0.21 (el piso teórico es 1/7≈0.14),
así que casi no distingue casos seguros de dudosos. Se sigue calculando y guardando, pero las decisiones usan el
**margen** entre la 1ª y la 2ª clase (`CHAT_INTENT_MIN_MARGIN = 1.5`): saludos/despedidas puros dan ≥1.75 y
mensajes mixtos como *"hola, tienen delivery"* dan ≤0.35, por lo que van a Gemini.

---

## 5. Pruebas

```bash
python manage.py test
```
18 pruebas (Gemini simulado, no consumen cuota): flujo del chat, historial, validaciones, CSRF, rate limit,
fallback, forma exacta de la llamada a Gemini, carga de datos idempotente y páginas del catálogo.

---

## 6. Personalizar los datos

- Productos y servicios: edítalos en `/admin/` (el chatbot los lee en ≤60 s) o modifica
  `catalog/seed_data.py` y vuelve a correr `python manage.py seed_data` (idempotente).
- Datos de la tienda (nombre, WhatsApp, horario): variables `STORE_*` en el `.env`.
- Nuevas intenciones/patrones: edita `chat/ml/intents.json` y ejecuta `python manage.py train_intents`.
- Tono y reglas del bot: `chat/services/prompt_builder.py`.

> Los productos, precios y políticas incluidos son **datos de ejemplo ficticios**. Los de horario, cambios en 7 días
> y envíos (Olva/Shalom) provienen del dataset de tu notebook; revísalos antes de publicar.

---

## 7. Recomendaciones

### Seguridad
- **Rota la clave** si alguna vez se subió a Git/Colab. Restringe la clave en Google AI Studio/Cloud (cuota y, si aplica, APIs permitidas) y fija un límite de gasto.
- `.env` está en `.gitignore`. En producción usa el gestor de secretos de tu hosting en vez de un archivo.
- Producción: `DJANGO_DEBUG=False`, `DJANGO_SECRET_KEY` larga y aleatoria, `DJANGO_ALLOWED_HOSTS` y `DJANGO_CSRF_TRUSTED_ORIGINS` reales (con `DEBUG=False` se activan HTTPS, cookies seguras y HSTS).
- **Prompt injection:** el prompt prohíbe cambiar de rol o revelar instrucciones, pero ninguna instrucción es infalible: no pongas secretos ni datos personales en el prompt, y no le des a Gemini herramientas que modifiquen datos sin validación propia.
- El texto del usuario se muestra con `textContent` y la respuesta del bot se escapa antes de dar formato (sin XSS). Mantén ese patrón.
- Los límites actuales (800 caracteres, 15 mensajes/min por sesión) protegen tu cuota. Una sesión se renueva borrando cookies, así que para abuso real añade límite por IP (p. ej. `django-ratelimit`) y CAPTCHA.
- Tus conversaciones contienen datos de clientes: define cuánto tiempo se conservan y avisa en tu política de privacidad.

### Rendimiento
- `GEMINI_THINKING_LEVEL=low` reduce latencia y costo; sube a `medium` si notas respuestas flojas.
- El catálogo se cachea 60 s. Cambia `LocMemCache` por **Redis** en producción (también para el rate limit, que con varios procesos en memoria local no se comparte).
- Con muchos productos (cientos) deja de ser viable meter todo el catálogo en el prompt: usa *function calling* para que Gemini consulte la BD, o búsqueda semántica con embeddings.
- Despliega con `gunicorn` + `whitenoise` (estáticos) y base PostgreSQL en lugar de SQLite.
- La llamada a Gemini es síncrona (típicamente 1-3 s). Para mucho tráfico, usa workers asíncronos o Celery.

### Mejoras posibles
- **Streaming** de la respuesta (SSE) para que el texto aparezca mientras se genera.
- **Function calling** para consultar stock/precio exacto y estado de pedidos reales.
- Derivación a un asesor humano (WhatsApp) cuando la intención sea `contacto` o el cliente se frustre.
- Botones "👍/👎" por respuesta y panel de métricas (consultas sin respuesta, intenciones más frecuentes).
- Reentrenar el clasificador con las conversaciones reales guardadas (`Message.intent`).
- Carrito/pedidos reales y autenticación de clientes.

---

## 8. Solución de problemas

| Síntoma | Causa / solución |
|---|---|
| El bot responde "Ahora mismo no puedo responder…" | Revisa la consola: `GEMINI_API_KEY no está configurada` (falta/placeholder en `.env`), o el error HTTP de Gemini (401/403 clave inválida, 429 cuota, 404 modelo). Reinicia `runserver` tras editar el `.env`. |
| `Modelo de intenciones no encontrado` | Ejecuta `python manage.py train_intents`. Es solo un aviso: el bot sigue con Gemini. |
| `ModuleNotFoundError: dotenv` / `google` | El entorno virtual no está activo o falta `pip install -r requirements.txt`. |
| Error 403 CSRF en el chat | Recarga la página (el token vive en la página y la cookie de sesión). |
| Cambié de versión de scikit-learn | Vuelve a ejecutar `train_intents` (el `.joblib` depende de la versión). |
