from django.db import models
from django.conf import settings
from django.contrib.contenttypes.models import ContentType
from django.contrib.contenttypes.fields import GenericForeignKey
    
User = settings.AUTH_USER_MODEL

class Project(models.Model):
    title = models.CharField('Название проекта', max_length=100)
    description = models.TextField('Описание проекта')
    created_by = models.ForeignKey(User, on_delete=models.CASCADE, null=True, blank=True, related_name='Проекты')
    created_at = models.DateTimeField('Дата создания',auto_now_add=True)
    
    class Meta:
        verbose_name = 'Проект'
        verbose_name_plural = 'Проекты'
        
    def __str__(self):
        return self.title
    
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
    
    title = models.CharField('Название задачи', max_length=100)
    description = models.TextField('Описание задачи')
    project = models.ForeignKey(Project, on_delete=models.CASCADE, null=True, blank=True, related_name='Проекты', verbose_name="Проект")
    assigned_to = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, 
                                  related_name='assigned_tasks', verbose_name="Исполнитель")
    
    created_by = models.ForeignKey(User, on_delete=models.CASCADE, related_name='created_tasks', verbose_name="Создан кем")
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='todo', verbose_name="Статус")
    priority = models.CharField(max_length=10, choices=PRIORITY_CHOICES, default='medium', verbose_name="Приоритет")
    due_date = models.DateField(null=True, blank=True, verbose_name="Срок выполнения")
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    def __str__(self):
        return self.title
    
    class Meta:
        ordering = ['-created_at']
    
    class Meta:
        verbose_name = 'Задача'
        verbose_name_plural = 'Задачи'