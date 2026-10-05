import json
from unittest.mock import patch

from django.core.cache import cache
from django.core.management import call_command
from django.test import Client, TestCase, override_settings
from django.urls import reverse

from chat.models import Conversation, Message
from chat.services.chatbot import ChatbotService, GeminiNotConfigured
from chat.services.intent_classifier import IntentResult


def post_json(client, url, payload):
    return client.post(url, data=json.dumps(payload), content_type="application/json")


class ChatApiTests(TestCase):
    def setUp(self):
        cache.clear()
        call_command("seed_data", verbosity=0)
        self.client = Client(enforce_csrf_checks=False)
        self.url = reverse("chat:send")

    def test_home_renders(self):
        self.assertEqual(self.client.get(reverse("chat:home")).status_code, 200)

    @patch("chat.services.chatbot.intent_classifier.predict", return_value=IntentResult("precios", 0.2, 2.0))
    @patch.object(ChatbotService, "_call_gemini", return_value="El polo cuesta S/ 59.90")
    def test_message_uses_gemini_and_persists_history(self, mock_gemini, _):
        res = post_json(self.client, self.url, {"message": "¿Cuánto cuesta el polo?"})
        self.assertEqual(res.status_code, 200)
        self.assertEqual(res.json()["source"], "gemini")
        self.assertEqual(Message.objects.count(), 2)
        # segundo turno: el historial previo (2 mensajes) llega a Gemini
        post_json(self.client, self.url, {"message": "¿Y en talla M?"})
        history = mock_gemini.call_args_list[1].args[1]
        self.assertEqual(len(history), 2)
        self.assertEqual(Conversation.objects.count(), 1)

    @patch.object(ChatbotService, "_call_gemini", side_effect=RuntimeError("boom"))
    def test_gemini_error_returns_fallback_not_500(self, _):
        res = post_json(self.client, self.url, {"message": "¿Tienen jeans?"})
        self.assertEqual(res.status_code, 200)
        self.assertEqual(res.json()["source"], "fallback")

    @patch.object(ChatbotService, "_get_client", side_effect=GeminiNotConfigured("sin clave"))
    def test_missing_api_key_returns_fallback(self, _):
        res = post_json(self.client, self.url, {"message": "¿Tienen jeans?"})
        self.assertEqual(res.json()["source"], "fallback")

    @patch("chat.services.chatbot.intent_classifier.canned_response", return_value="¡Hola! 👋")
    @patch("chat.services.chatbot.intent_classifier.predict", return_value=IntentResult("saludo", 0.2, 2.2))
    @patch.object(ChatbotService, "_call_gemini")
    def test_short_greeting_skips_gemini(self, mock_gemini, *_):
        res = post_json(self.client, self.url, {"message": "hola"})
        self.assertEqual(res.json()["source"], "shortcut")
        mock_gemini.assert_not_called()

    @patch("chat.services.chatbot.intent_classifier.predict", return_value=IntentResult("saludo", 0.2, 2.2))
    @patch.object(ChatbotService, "_call_gemini", return_value="Claro, cuesta S/ 59.90")
    def test_greeting_plus_question_goes_to_gemini(self, mock_gemini, _):
        res = post_json(self.client, self.url, {"message": "hola, cuanto cuesta el polo basico?"})
        self.assertEqual(res.json()["source"], "gemini")

    def test_validation(self):
        self.assertEqual(post_json(self.client, self.url, {"message": "   "}).status_code, 400)
        self.assertEqual(post_json(self.client, self.url, {"message": "x" * 5000}).status_code, 400)
        res = self.client.post(self.url, data="no-json", content_type="application/json")
        self.assertEqual(res.status_code, 400)

    def test_get_not_allowed(self):
        self.assertEqual(self.client.get(self.url).status_code, 405)

    def test_csrf_enforced(self):
        strict = Client(enforce_csrf_checks=True)
        self.assertEqual(post_json(strict, self.url, {"message": "hola"}).status_code, 403)

    @override_settings(CHAT_RATE_LIMIT_PER_MINUTE=2)
    @patch.object(ChatbotService, "_call_gemini", return_value="ok")
    def test_rate_limit(self, _):
        codes = [post_json(self.client, self.url, {"message": f"m{i}"}).status_code for i in range(3)]
        self.assertEqual(codes, [200, 200, 429])

    @patch.object(ChatbotService, "_call_gemini", return_value="ok")
    def test_reset_starts_new_conversation(self, _):
        post_json(self.client, self.url, {"message": "uno"})
        self.client.post(reverse("chat:reset"))
        post_json(self.client, self.url, {"message": "dos"})
        self.assertEqual(Conversation.objects.count(), 2)


class GeminiCallShapeTests(TestCase):
    """Verifica los argumentos enviados a client.interactions.create (sin red)."""

    def setUp(self):
        call_command("seed_data", verbosity=0)

    @override_settings(GEMINI_API_KEY="clave-de-prueba", GEMINI_MODEL="gemini-3.8-flash")
    @patch("chat.services.chatbot.genai.Client")
    def test_interactions_call(self, mock_client_cls):
        mock_client_cls.return_value.interactions.create.return_value.output_text = " Hola cliente "
        history = [{"role": "assistant", "content": "stray"}, {"role": "user", "content": "a"},
                   {"role": "assistant", "content": "b"}]
        text = ChatbotService()._call_gemini("¿precio?", history, IntentResult("precios", 0.2, 2.0))

        self.assertEqual(text, "Hola cliente")
        mock_client_cls.assert_called_once_with(api_key="clave-de-prueba")
        kwargs = mock_client_cls.return_value.interactions.create.call_args.kwargs
        self.assertEqual(kwargs["model"], "gemini-3.8-flash")
        self.assertFalse(kwargs["store"])
        self.assertEqual([s["type"] for s in kwargs["input"]], ["user_input", "model_output", "user_input"])
        self.assertIn("Zapatillas Running AirFlex", kwargs["system_instruction"])
        self.assertIn("precios", kwargs["system_instruction"])

    @override_settings(GEMINI_API_KEY="")
    def test_no_key_raises(self):
        with self.assertRaises(GeminiNotConfigured):
            ChatbotService()._get_client()
