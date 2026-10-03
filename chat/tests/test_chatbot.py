import json
import shutil
import tempfile
from pathlib import Path

from django.conf import settings
from django.core.cache import cache
from django.test import Client, TestCase, override_settings

from chat.models import Conversation, Message
from chat.services.chatbot import ChatbotService, set_classifier
from chat.services.exceptions import InvalidMessageError, ModelNotTrainedError
from chat.services.intent_classifier import IntentClassifier
from chat.services.text_cleaner import TextCleaner
from chat.services.training import train_and_save

TMP_DIR = Path(tempfile.mkdtemp(prefix="chatbot-tests-"))
MODEL_PATH = TMP_DIR / "model.joblib"


def make_classifier(**kwargs) -> IntentClassifier:
    return IntentClassifier(MODEL_PATH, **kwargs)


class BaseChatTest(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        train_and_save(settings.CHATBOT["INTENTS_PATH"], MODEL_PATH, quick=True)

    @classmethod
    def tearDownClass(cls):
        shutil.rmtree(TMP_DIR, ignore_errors=True)
        super().tearDownClass()

    def setUp(self):
        cache.clear()
        set_classifier(make_classifier(min_confidence=0.0, min_margin=0.10))

    def tearDown(self):
        set_classifier(None)

    def post(self, client, message):
        return client.post("/api/chat/", data=json.dumps({"message": message}), content_type="application/json")


class TextCleanerTests(TestCase):
    def test_normaliza_tildes_urls_numeros_y_simbolos(self):
        out = TextCleaner().transform(["¡Hola! Visita http://x.com, ¿cuánto cuesta 25 soles?"])
        self.assertEqual(out, ["hola visita cuanto cuesta soles"])


class ClassifierTests(BaseChatTest):
    def test_intenciones_claras(self):
        clf = make_classifier(min_margin=0.10)
        self.assertEqual(clf.predict("Hola, buenos dias").intent, "saludo")
        self.assertEqual(clf.predict("Quiero saber el estado de mi envio").intent, "envio")
        self.assertEqual(clf.predict("Muchas gracias, hasta luego").intent, "despedida")

    def test_ruido_cae_en_fallback(self):
        pred = make_classifier(min_margin=0.10).predict("asdfgh qwerty zxcv")
        self.assertIsNone(pred.intent)

    def test_modelo_inexistente(self):
        with self.assertRaises(ModelNotTrainedError):
            IntentClassifier(TMP_DIR / "no-existe.joblib").predict("hola")


class ServiceTests(BaseChatTest):
    def test_valida_mensajes(self):
        service = ChatbotService()
        for bad in ["", "   ", None, 123, "x" * 501]:
            with self.assertRaises(InvalidMessageError):
                service.validate(bad)

    def test_persiste_ambos_mensajes_y_no_repite_respuesta_consecutiva(self):
        conv = Conversation.objects.create()
        service = ChatbotService()
        answers = [service.reply(conv, "hola").text for _ in range(6)]
        self.assertEqual(conv.messages.count(), 12)
        self.assertTrue(all(a != b for a, b in zip(answers, answers[1:])))


class ApiTests(BaseChatTest):
    def test_index_ok(self):
        self.assertEqual(Client().get("/").status_code, 200)

    def test_flujo_completo_e_historial(self):
        client = Client()
        client.get("/")
        r = self.post(client, "cual es el horario de atencion")
        self.assertEqual(r.status_code, 200)
        self.assertEqual(r.json()["intent"], "horario")
        self.assertEqual(len(client.get("/api/history/").json()["messages"]), 2)

    def test_historial_aislado_por_sesion(self):
        a, b = Client(), Client()
        self.post(a, "hola")
        self.assertEqual(len(a.get("/api/history/").json()["messages"]), 2)
        self.assertEqual(len(b.get("/api/history/").json()["messages"]), 0)

    def test_reset_inicia_conversacion_nueva(self):
        client = Client()
        self.post(client, "hola")
        client.post("/api/reset/")
        self.assertEqual(len(client.get("/api/history/").json()["messages"]), 0)
        self.assertEqual(Conversation.objects.count(), 2)  # la anterior se conserva

    def test_errores_de_validacion(self):
        client = Client()
        self.assertEqual(self.post(client, "").status_code, 400)
        self.assertEqual(client.post("/api/chat/", data="no-json", content_type="application/json").status_code, 400)
        self.assertEqual(client.post("/api/chat/", data="[1,2]", content_type="application/json").status_code, 400)
        self.assertEqual(client.get("/api/chat/").status_code, 405)

    def test_modelo_no_entrenado_devuelve_503_sin_basura_en_bd(self):
        set_classifier(IntentClassifier(TMP_DIR / "no-existe.joblib"))
        r = self.post(Client(), "hola")
        self.assertEqual(r.status_code, 503)
        self.assertEqual(Message.objects.count(), 0)

    def test_csrf_se_exige(self):
        client = Client(enforce_csrf_checks=True)
        r = client.post("/api/chat/", data=json.dumps({"message": "hola"}), content_type="application/json")
        self.assertEqual(r.status_code, 403)

    def test_rate_limit(self):
        client = Client()
        with override_settings(CHATBOT={**settings.CHATBOT, "RATE_LIMIT_PER_MINUTE": 3}):
            codes = [self.post(client, "hola").status_code for _ in range(5)]
        self.assertEqual(codes, [200, 200, 200, 429, 429])
