from django.core.management.base import BaseCommand
from django.db import transaction

from catalog.models import Category, Offering, Product
from catalog.seed_data import CATEGORIES, OFFERINGS, PRODUCTS


class Command(BaseCommand):
    help = "Carga (o actualiza) los productos y servicios de ejemplo. Es idempotente."

    @transaction.atomic
    def handle(self, *args, **options):
        categories = {name: Category.objects.get_or_create(name=name)[0] for name in CATEGORIES}

        for data in PRODUCTS:
            data = dict(data)
            category = categories[data.pop("category")]
            sku = data.pop("sku")
            Product.objects.update_or_create(sku=sku, defaults={**data, "category": category})

        for data in OFFERINGS:
            data = dict(data)
            name = data.pop("name")
            Offering.objects.update_or_create(name=name, defaults=data)

        if options["verbosity"] > 0:
            self.stdout.write(self.style.SUCCESS(
                f"Datos cargados: {Product.objects.count()} productos, "
                f"{Offering.objects.count()} servicios/beneficios, {Category.objects.count()} categorías."
            ))
