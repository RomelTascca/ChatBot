from django.urls import path

from . import views

app_name = "chat"

urlpatterns = [
    path("", views.chat_page, name="home"),
    path("chat/api/send/", views.send_message, name="send"),
    path("chat/api/reset/", views.reset_conversation, name="reset"),
]
