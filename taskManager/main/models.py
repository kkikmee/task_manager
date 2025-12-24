from django.db import models
from django.conf import settings
from django.contrib.contenttypes.models import ContentType
from django.contrib.contenttypes.fields import GenericForeignKey
    
User = settings.AUTH_USER_MODEL

class Project(models.Model):
    name = models.CharField(max_length=100, verbose_name="Название проекта")
    description = models.TextField(blank=True, verbose_name="Описание")
    created_by = models.ForeignKey(User, on_delete=models.CASCADE, related_name='created_projects')
    team_members = models.ManyToManyField(
        User, 
        through='ProjectMembership',
        through_fields=('project', 'user'),
        related_name='projects'
    )
    created_at = models.DateTimeField(auto_now_add=True)
    color = models.CharField(max_length=7, default='#007bff', verbose_name="Цвет")
    
    def __str__(self):
        return self.name
    
    def get_team_members(self):
        """Возвращает всех участников проекта с их ролями"""
        return self.projectmembership_set.select_related('user')
    
    def is_user_in_project(self, user):
        """Проверяет, является ли пользователь участником проекта"""
        return self.team_members.filter(id=user.id).exists() or self.created_by == user
    
    class Meta:
        ordering = ['name']

class ProjectMembership(models.Model):
    ROLE_CHOICES = [
        ('manager', 'Менеджер'),
        ('developer', 'Разработчик'),
        ('designer', 'Дизайнер'),
        ('tester', 'Тестировщик'),
        ('viewer', 'Наблюдатель'),
    ]
    
    project = models.ForeignKey(Project, on_delete=models.CASCADE)
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    role = models.CharField(max_length=20, choices=ROLE_CHOICES, default='developer')
    joined_at = models.DateTimeField(auto_now_add=True)
    can_edit_tasks = models.BooleanField(default=False, verbose_name="Может редактировать задачи")
    can_invite_users = models.BooleanField(default=False, verbose_name="Может приглашать пользователей")
    
    class Meta:
        unique_together = ['project', 'user']  # Один пользователь - одна роль в проекте
        ordering = ['-joined_at']
    
    def __str__(self):
        return f"{self.user.username} - {self.project.name} ({self.get_role_display()})"
    
# models.py
class Task(models.Model):
    STATUS_CHOICES = [
        ('todo', 'К выполнению'),
        ('in_progress', 'В процессе'),
        ('review', 'На проверке'),
        ('done', 'Выполнено'),
    ]
    
    PRIORITY_CHOICES = [
        ('low', 'Низкий'),
        ('medium', 'Средний'),
        ('high', 'Высокий'),
    ]
    
    title = models.CharField(max_length=200, verbose_name="Задача")
    description = models.TextField(blank=True, verbose_name="Описание")
    project = models.ForeignKey(Project, on_delete=models.CASCADE, related_name='tasks')
    
    # ИСПРАВЛЕННОЕ поле assigned_to - убрана сложная валидация
    assigned_to = models.ForeignKey(
        User, 
        on_delete=models.SET_NULL, 
        null=True, 
        blank=True,
        related_name='assigned_tasks', 
        verbose_name="Исполнитель"
    )
    
    created_by = models.ForeignKey(User, on_delete=models.CASCADE, related_name='created_tasks')
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='todo', verbose_name="Статус")
    priority = models.CharField(max_length=10, choices=PRIORITY_CHOICES, default='medium', verbose_name="Приоритет")
    due_date = models.DateField(null=True, blank=True, verbose_name="Срок выполнения")
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    def __str__(self):
        return self.title
    
    def save(self, *args, **kwargs):
        """Проверяем, что исполнитель состоит в проекте"""
        if self.assigned_to and not self.project.is_user_in_project(self.assigned_to):
            raise ValueError("Исполнитель должен быть участником проекта")
        super().save(*args, **kwargs)
    
    class Meta:
        ordering = ['-created_at']