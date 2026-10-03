from django.contrib import admin

from .models import Conversation, Message


class MessageInline(admin.TabularInline):
    model = Message
    extra = 0
    readonly_fields = ("role", "content", "intent", "confidence", "created_at")
    can_delete = False


@admin.register(Conversation)
class ConversationAdmin(admin.ModelAdmin):
    list_display = ("id", "user", "created_at", "updated_at")
    inlines = [MessageInline]


@admin.register(Message)
class MessageAdmin(admin.ModelAdmin):
    list_display = ("conversation", "role", "short_content", "intent", "confidence", "created_at")
    list_filter = ("role", "intent")
    search_fields = ("content",)

    @admin.display(description="Contenido")
    def short_content(self, obj):
        return obj.content[:60]
