from django.conf import settings
from django.core.management.base import BaseCommand, CommandError

from chat.services.chatbot import set_classifier
from chat.services.training import train_and_save


class Command(BaseCommand):
    help = "Entrena el clasificador de intenciones (TF-IDF + LinearSVC) y guarda el artefacto .joblib."

    def add_arguments(self, parser):
        parser.add_argument("--quick", action="store_true",
                            help="Usa una rejilla de hiperparámetros reducida (desarrollo/tests).")

    def handle(self, *args, **options):
        cfg = settings.CHATBOT
        if not cfg["INTENTS_PATH"].exists():
            raise CommandError(f"No se encontró el dataset: {cfg['INTENTS_PATH']}")

        self.stdout.write("Entrenando modelo... (GridSearchCV puede tardar un poco)")
        metrics = train_and_save(cfg["INTENTS_PATH"], cfg["MODEL_PATH"], quick=options["quick"])
        set_classifier(None)  # fuerza recarga en este proceso

        self.stdout.write(f"Mejores hiperparámetros: {metrics['best_params']}")
        self.stdout.write(f"Accuracy entrenamiento: {metrics['accuracy_train']:.4f}")
        self.stdout.write(f"Accuracy prueba:        {metrics['accuracy_test']:.4f}\n")
        self.stdout.write(metrics["report"])
        self.stdout.write(self.style.SUCCESS(f"Modelo guardado en {cfg['MODEL_PATH']}"))
