from django.contrib import admin

from .models import Category, Offering, Product


@admin.register(Category)
class CategoryAdmin(admin.ModelAdmin):
    list_display = ("name", "slug")
    prepopulated_fields = {"slug": ("name",)}


@admin.register(Product)
class ProductAdmin(admin.ModelAdmin):
    list_display = ("name", "sku", "category", "price", "stock", "is_featured", "is_active")
    list_filter = ("category", "is_active", "is_featured")
    search_fields = ("name", "sku", "description")
    list_editable = ("price", "stock", "is_active")


@admin.register(Offering)
class OfferingAdmin(admin.ModelAdmin):
    list_display = ("name", "kind", "highlight", "order", "is_active")
    list_filter = ("kind", "is_active")
    list_editable = ("order", "is_active")
