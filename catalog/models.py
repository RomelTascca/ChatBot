from django.db import models
from django.utils.text import slugify


class Category(models.Model):
    name = models.CharField("nombre", max_length=60, unique=True)
    slug = models.SlugField(max_length=70, unique=True, blank=True)

    class Meta:
        verbose_name = "categoría"
        verbose_name_plural = "categorías"
        ordering = ["name"]

    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = slugify(self.name)
        super().save(*args, **kwargs)

    def __str__(self):
        return self.name


class Product(models.Model):
    sku = models.CharField("SKU", max_length=20, unique=True)
    name = models.CharField("nombre", max_length=120)
    slug = models.SlugField(max_length=140, unique=True, blank=True)
    description = models.TextField("descripción")
    category = models.ForeignKey(Category, on_delete=models.PROTECT, related_name="products", verbose_name="categoría")
    price = models.DecimalField("precio (S/)", max_digits=8, decimal_places=2)
    old_price = models.DecimalField("precio anterior (S/)", max_digits=8, decimal_places=2, null=True, blank=True)
    stock = models.PositiveIntegerField(default=0)
    sizes = models.CharField("tallas / variantes", max_length=80, blank=True, help_text="Ej: S, M, L, XL")
    image_url = models.URLField("imagen (URL)", blank=True)
    emoji = models.CharField(max_length=4, blank=True, default="🛍️")
    is_featured = models.BooleanField("destacado", default=False)
    is_active = models.BooleanField("activo", default=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = "producto"
        verbose_name_plural = "productos"
        ordering = ["category__name", "name"]

    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = slugify(self.name)
        super().save(*args, **kwargs)

    @property
    def in_stock(self) -> bool:
        return self.stock > 0

    @property
    def discount_percent(self) -> int | None:
        if self.old_price and self.old_price > self.price:
            return int(round((1 - self.price / self.old_price) * 100))
        return None

    def __str__(self):
        return self.name


class Offering(models.Model):
    """Lo que la tienda ofrece: servicios, beneficios, planes, funcionalidades, promociones."""

    class Kind(models.TextChoices):
        SERVICE = "servicio", "Servicio"
        BENEFIT = "beneficio", "Beneficio"
        PLAN = "plan", "Plan"
        FEATURE = "funcionalidad", "Funcionalidad"
        PROMO = "promocion", "Promoción"

    name = models.CharField("nombre", max_length=120, unique=True)
    kind = models.CharField("tipo", max_length=20, choices=Kind.choices)
    description = models.TextField("descripción")
    highlight = models.CharField("dato clave", max_length=120, blank=True, help_text="Ej: Gratis desde S/ 199")
    icon = models.CharField(max_length=4, blank=True, default="✨")
    order = models.PositiveSmallIntegerField("orden", default=0)
    is_active = models.BooleanField("activo", default=True)

    class Meta:
        verbose_name = "servicio / beneficio"
        verbose_name_plural = "servicios y beneficios"
        ordering = ["order", "name"]

    def __str__(self):
        return f"{self.get_kind_display()}: {self.name}"
