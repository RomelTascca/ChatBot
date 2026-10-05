from django.urls import path

from . import views

app_name = "catalog"

urlpatterns = [
    path("productos/", views.product_list, name="product_list"),
    path("servicios/", views.offering_list, name="offering_list"),
]
