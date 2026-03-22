from django.contrib import admin
from Ai.models import MissingQuestion

@admin.register(MissingQuestion)
class MissingQuestionAdmin(admin.ModelAdmin):
    list_display = ['question', 'language', 'detected_language', 'asked_count', 'first_asked', 'is_resolved']
    list_filter = ['language', 'is_resolved', 'detected_language']
    search_fields = ['question']
    ordering = ['-asked_count']
    list_editable = ['is_resolved']
    readonly_fields = ['first_asked', 'last_asked', 'asked_count']
