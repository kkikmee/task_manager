# admin.py
from django.contrib import admin
from django.utils.html import format_html
from .models import Project, Task

# Настройки для админ-панели
@admin.register(Project)
class ProjectAdmin(admin.ModelAdmin):
    list_display = ('title', 'created_by', 'created_at')
    list_filter = ('created_at', 'created_by')
    search_fields = ('title', 'description')
    readonly_fields = ('created_at',)

@admin.register(Task)
class TaskAdmin(admin.ModelAdmin):
    list_display = (
        'title', 
        'project',
        'assigned_to', 
        'created_by',
        'due_date',
    )
    list_filter = (
        'status', 
        'priority', 
        'due_date',
        'created_at',
        'project',
        'assigned_to'
    )
    search_fields = ('title', 'description', 'project__name')
    readonly_fields = ('created_at', 'updated_at')
    list_per_page = 25
    
    