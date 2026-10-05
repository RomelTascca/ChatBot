from django.core.management import call_command
from django.test import TestCase
from django.urls import reverse

from .models import Offering, Product


class CatalogTests(TestCase):
    def setUp(self):
        call_command("seed_data", verbosity=0)

    def test_seed_loads_enough_data_and_is_idempotent(self):
        self.assertGreaterEqual(Product.objects.count(), 10)
        self.assertGreaterEqual(Offering.objects.count(), 10)
        call_command("seed_data", verbosity=0)
        self.assertEqual(Product.objects.count(), 12)

    def test_pages_render(self):
        self.assertContains(self.client.get(reverse("catalog:product_list")), "Zapatillas Running AirFlex")
        self.assertContains(self.client.get(reverse("catalog:offering_list")), "Delivery Lima Express")

    def test_prices_use_decimal_point(self):
        self.assertContains(self.client.get(reverse("catalog:product_list")), "S/ 249.90")

    def test_filters(self):
        res = self.client.get(reverse("catalog:product_list"), {"categoria": "tecnologia", "q": "power"})
        self.assertContains(res, "Power Bank")
        self.assertNotContains(res, "Polo Algodón")

    def test_discount_and_stock_flags(self):
        self.assertEqual(Product.objects.get(sku="CAL-001").discount_percent, 17)
        self.assertFalse(Product.objects.get(sku="ROP-002").in_stock)
