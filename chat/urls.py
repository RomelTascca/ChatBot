from django.urls import path

from . import views

app_name = "chat"

urlpatterns = [
    path("", views.index, name="index"),
    path("api/chat/", views.send_message, name="send_message"),
    path("api/history/", views.history, name="history"),
    path("api/reset/", views.reset, name="reset"),
]
