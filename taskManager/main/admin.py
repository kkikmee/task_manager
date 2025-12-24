# admin.py
from django.contrib import admin
from django.contrib.auth import get_user_model
from django.utils.html import format_html
from django.urls import path
from django.shortcuts import render, redirect
from django.contrib import messages
from django.http import HttpResponseRedirect
from .models import Project, Task, ProjectMembership
from django.conf import settings

User = settings.AUTH_USER_MODEL
User = get_user_model()

# Кастомный фильтр для проектов
class ProjectCreatorFilter(admin.SimpleListFilter):
    title = 'Создатель проекта'
    parameter_name = 'creator'
    
    def lookups(self, request, model_admin):
        creators = User.objects.filter(created_projects__isnull=False).distinct()
        return [(user.id, user.username) for user in creators]
    
    def queryset(self, request, queryset):
        if self.value():
            return queryset.filter(created_by_id=self.value())
        return queryset

# Кастомный фильтр для задач по проектам
class TaskProjectFilter(admin.SimpleListFilter):
    title = 'Проект'
    parameter_name = 'project'
    
    def lookups(self, request, model_admin):
        projects = Project.objects.all()
        return [(project.id, project.name) for project in projects]
    
    def queryset(self, request, queryset):
        if self.value():
            return queryset.filter(project_id=self.value())
        return queryset

# Inline для отображения участников проекта в админке
class ProjectMembershipInline(admin.TabularInline):
    model = ProjectMembership
    extra = 1
    fields = ('user', 'role', 'can_edit_tasks', 'can_invite_users', 'joined_at')
    readonly_fields = ('joined_at',)
    raw_id_fields = ('user',)
    
    def get_queryset(self, request):
        return super().get_queryset(request).select_related('user')

# Inline для отображения задач проекта в админке
class TaskInline(admin.TabularInline):
    model = Task
    extra = 0
    fields = ('title', 'assigned_to', 'status', 'priority', 'due_date')
    readonly_fields = ('created_at',)
    show_change_link = True
    
    def get_queryset(self, request):
        return super().get_queryset(request).select_related('assigned_to')

# Кастомная админка для ProjectMembership
@admin.register(ProjectMembership)
class ProjectMembershipAdmin(admin.ModelAdmin):
    list_display = (
        'project_name', 
        'user', 
        'role_badge', 
        'permissions_display', 
        'joined_at', 
        'is_active'
    )
    list_filter = ('role', 'joined_at', 'project', 'can_edit_tasks', 'can_invite_users')
    search_fields = ('user__username', 'user__email', 'project__name')
    readonly_fields = ('joined_at',)
    list_select_related = ('project', 'user')
    list_per_page = 50
    
    fieldsets = (
        ('Основная информация', {
            'fields': ('project', 'user', 'role')
        }),
        ('Права доступа', {
            'fields': ('can_edit_tasks', 'can_invite_users'),
            'classes': ('collapse',)
        }),
        ('Системная информация', {
            'fields': ('joined_at',),
            'classes': ('collapse',)
        }),
    )
    
    def project_name(self, obj):
        return obj.project.name
    project_name.short_description = 'Проект'
    project_name.admin_order_field = 'project__name'
    
    def role_badge(self, obj):
        role_colors = {
            'manager': 'danger',
            'developer': 'warning',
            'designer': 'info',
            'tester': 'secondary',
            'viewer': 'success',
        }
        color = role_colors.get(obj.role, 'secondary')
        return format_html(
            '<span class="badge bg-{}">{}</span>',
            color,
            obj.get_role_display()
        )
    role_badge.short_description = 'Роль'
    
    def permissions_display(self, obj):
        permissions = []
        if obj.can_edit_tasks:
            permissions.append('📝 Редакт.')
        if obj.can_invite_users:
            permissions.append('👥 Приглаш.')
        return format_html(' '.join(permissions)) if permissions else '—'
    permissions_display.short_description = 'Права'
    
    def is_active(self, obj):
        return obj.user.is_active
    is_active.short_description = 'Активен'
    is_active.boolean = True

# Кастомная админка для Project
@admin.register(Project)
class ProjectAdmin(admin.ModelAdmin):
    list_display = (
        'name', 
        'created_by', 
        'team_members_count', 
        'tasks_count', 
        'created_at', 
        'color_preview'
    )
    list_filter = (ProjectCreatorFilter, 'created_at')
    search_fields = ('name', 'description', 'created_by__username')
    readonly_fields = ('created_at', 'tasks_count_display', 'team_members_list')
    list_select_related = ('created_by',)
    inlines = [ProjectMembershipInline]
    list_per_page = 25
    
    fieldsets = (
        ('Основная информация', {
            'fields': ('name', 'description', 'color', 'created_by')
        }),
        ('Статистика', {
            'fields': ('tasks_count_display', 'team_members_list'),
            'classes': ('collapse',)
        }),
        ('Системная информация', {
            'fields': ('created_at',),
            'classes': ('collapse',)
        }),
    )
    
    def team_members_count(self, obj):
        count = obj.team_members.count()
        return format_html(
            '<span class="badge bg-info">{}</span>',
            count
        )
    team_members_count.short_description = 'Участников'
    
    def tasks_count(self, obj):
        count = obj.tasks.count()
        color = 'success' if count > 0 else 'secondary'
        return format_html(
            '<span class="badge bg-{}">{}</span>',
            color,
            count
        )
    tasks_count.short_description = 'Задач'
    
    def tasks_count_display(self, obj):
        return obj.tasks.count()
    tasks_count_display.short_description = 'Всего задач'
    
    def team_members_list(self, obj):
        members = obj.projectmembership_set.select_related('user')[:10]
        if not members:
            return "Нет участников"
        
        member_list = []
        for membership in members:
            member_list.append(
                f"{membership.user.username} ({membership.get_role_display()})"
            )
        return format_html("<br>".join(member_list))
    team_members_list.short_description = 'Участники проекта'
    
    def color_preview(self, obj):
        return format_html(
            '<div style="width: 30px; height: 20px; background-color: {}; border: 1px solid #ccc; border-radius: 3px;"></div>',
            obj.color
        )
    color_preview.short_description = 'Цвет'
    
    # Кастомное действие для массового добавления пользователей
    def add_users_action(self, request, queryset):
        if queryset.count() != 1:
            self.message_user(request, "Выберите только один проект", messages.ERROR)
            return HttpResponseRedirect(request.get_full_path())
        
        project = queryset.first()
        return redirect('admin:project_add_users', project_id=project.id)
    add_users_action.short_description = "Добавить пользователей в проект"
    
    def get_urls(self):
        urls = super().get_urls()
        custom_urls = [
            path(
                '<int:project_id>/add-users/',
                self.admin_site.admin_view(self.add_users_view),
                name='project_add_users',
            ),
        ]
        return custom_urls + urls
    
    def add_users_view(self, request, project_id):
        project = Project.objects.get(id=project_id)
        
        if request.method == 'POST':
            user_ids = request.POST.getlist('users')
            role = request.POST.get('role', 'developer')
            
            for user_id in user_ids:
                user = User.objects.get(id=user_id)
                ProjectMembership.objects.get_or_create(
                    project=project,
                    user=user,
                    defaults={'role': role}
                )
            
            self.message_user(request, f"Пользователи добавлены в проект {project.name}", messages.SUCCESS)
            return redirect('admin:tasks_project_changelist')
        
        # Показываем только пользователей, которых еще нет в проекте
        existing_user_ids = project.team_members.values_list('id', flat=True)
        available_users = User.objects.filter(is_active=True).exclude(id__in=existing_user_ids)
        
        context = {
            **self.admin_site.each_context(request),
            'project': project,
            'available_users': available_users,
            'opts': self.model._meta,
            'title': f'Добавить пользователей в {project.name}',
        }
        return render(request, 'admin/tasks/project_add_users.html', context)
    
    actions = [add_users_action]

# Кастомный фильтр для статуса срока задач
class TaskDueDateFilter(admin.SimpleListFilter):
    title = 'Статус срока'
    parameter_name = 'due_status'
    
    def lookups(self, request, model_admin):
        return (
            ('overdue', '⚠️ Просроченные'),
            ('today', '📅 На сегодня'),
            ('week', '🗓️ На неделю'),
            ('future', '⏳ Будущие'),
            ('no_date', '❓ Без срока'),
        )
    
    def queryset(self, request, queryset):
        from django.utils import timezone
        from datetime import timedelta
        
        if self.value() == 'overdue':
            return queryset.filter(due_date__lt=timezone.now().date(), status__in=['todo', 'in_progress'])
        elif self.value() == 'today':
            return queryset.filter(due_date=timezone.now().date())
        elif self.value() == 'week':
            week_end = timezone.now().date() + timedelta(days=7)
            return queryset.filter(due_date__range=[timezone.now().date(), week_end])
        elif self.value() == 'future':
            return queryset.filter(due_date__gt=timezone.now().date())
        elif self.value() == 'no_date':
            return queryset.filter(due_date__isnull=True)
        return queryset

# Кастомная админка для Task
@admin.register(Task)
class TaskAdmin(admin.ModelAdmin):
    list_display = (
        'title_truncated',
        'project_link',
        'assigned_to',
        'status',
        'priority',
        'status_badge',
        'priority_badge',
        'due_date_display',
        'created_by',
        'created_at_short',
    )
    list_filter = (
        TaskProjectFilter,
        'status',
        'priority',
        TaskDueDateFilter,
        'created_at',
        'assigned_to',
    )
    search_fields = ('title', 'description', 'project__name', 'assigned_to__username')
    readonly_fields = ('created_at', 'updated_at', 'created_by_display')
    list_editable = ('status', 'priority')
    list_select_related = ('project', 'assigned_to', 'created_by')
    list_per_page = 30
    raw_id_fields = ('assigned_to',)
    
    fieldsets = (
        ('Основная информация', {
            'fields': ('title', 'description', 'project')
        }),
        ('Исполнение', {
            'fields': ('assigned_to', 'status', 'priority', 'due_date')
        }),
        ('Системная информация', {
            'fields': ('created_by_display', 'created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )
    
    def title_truncated(self, obj):
        return obj.title[:50] + '...' if len(obj.title) > 50 else obj.title
    title_truncated.short_description = 'Задача'
    title_truncated.admin_order_field = 'title'
    
    def project_link(self, obj):
        return format_html(
            '<a href="{}">{}</a>',
            f'../project/{obj.project.id}/change/',
            obj.project.name
        )
    project_link.short_description = 'Проект'
    project_link.admin_order_field = 'project__name'
    
    def status_badge(self, obj):
        status_colors = {
            'todo': 'secondary',
            'in_progress': 'warning',
            'review': 'info',
            'done': 'success',
        }
        color = status_colors.get(obj.status, 'secondary')
        return format_html(
            '<span class="badge bg-{}">{}</span>',
            color,
            obj.get_status_display()
        )
    status_badge.short_description = 'Статус'
    
    def priority_badge(self, obj):
        priority_colors = {
            'low': 'success',
            'medium': 'warning',
            'high': 'danger',
        }
        color = priority_colors.get(obj.priority, 'secondary')
        return format_html(
            '<span class="badge bg-{}">{}</span>',
            color,
            obj.get_priority_display()
        )
    priority_badge.short_description = 'Приоритет'
    
    def due_date_display(self, obj):
        if not obj.due_date:
            return format_html('<span class="text-muted">—</span>')
        
        from django.utils import timezone
        if obj.due_date < timezone.now().date() and obj.status != 'done':
            return format_html(
                '<span style="color: red; font-weight: bold;">{} ⚠️</span>',
                obj.due_date.strftime('%d.%m.%Y')
            )
        return obj.due_date.strftime('%d.%m.%Y')
    due_date_display.short_description = 'Срок'
    due_date_display.admin_order_field = 'due_date'
    
    def created_by_display(self, obj):
        return obj.created_by.username
    created_by_display.short_description = 'Создатель'
    
    def created_at_short(self, obj):
        return obj.created_at.strftime('%d.%m.%Y')
    created_at_short.short_description = 'Создана'
    created_at_short.admin_order_field = 'created_at'
    
    # Автоматическое заполнение created_by
    def save_model(self, request, obj, form, change):
        if not obj.pk:
            obj.created_by = request.user
        super().save_model(request, obj, form, change)
    
    # Ограничение выбора исполнителей участниками проекта
    def formfield_for_foreignkey(self, db_field, request, **kwargs):
        if db_field.name == "assigned_to":
            # Можно добавить логику фильтрации по проекту
            kwargs["queryset"] = User.objects.filter(is_active=True).order_by('username')
        return super().formfield_for_foreignkey(db_field, request, **kwargs)
    
    # Кастомные действия для задач
    def mark_as_done(self, request, queryset):
        updated = queryset.update(status='done')
        self.message_user(request, f"{updated} задач отмечены как выполненные", messages.SUCCESS)
    mark_as_done.short_description = "Отметить как выполненные"
    
    def set_high_priority(self, request, queryset):
        updated = queryset.update(priority='high')
        self.message_user(request, f"{updated} задач установлен высокий приоритет", messages.SUCCESS)
    set_high_priority.short_description = "Установить высокий приоритет"
    
    def clear_due_dates(self, request, queryset):
        updated = queryset.update(due_date=None)
        self.message_user(request, f"{updated} задач очищены сроки", messages.SUCCESS)
    clear_due_dates.short_description = "Очистить сроки выполнения"
    
    actions = [mark_as_done, set_high_priority, clear_due_dates]

# Расширяем стандартную админку User

# Кастомные настройки админ-панели
admin.site.site_header = "🚀 Task Manager - Панель управления"
admin.site.site_title = "Task Manager Admin"
admin.site.index_title = "Управление проектами и задачами"

# Кастомный CSS для админки
class CustomAdminSite(admin.AdminSite):
    def each_context(self, request):
        context = super().each_context(request)
        context['site_header'] = '🚀 Task Manager'
        return context