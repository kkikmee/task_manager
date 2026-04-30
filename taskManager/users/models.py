from django.db import models
from django.contrib.auth.models import AbstractUser

class User(AbstractUser):
    avatar = models.ImageField(upload_to='users', null=True, blank=True, default='users/anonimuser.jpg')
    bio = models.TextField('Biography', null=True, blank=True)
    
    def __str__(self):
        return self.username

    def get_colleagues(self):
        """Возвращает всех подтверждённых коллег пользователя"""
        from django.db.models import Q
        accepted = ColleagueRequest.objects.filter(
            Q(from_user=self, status='accepted') |
            Q(to_user=self, status='accepted')
        ).select_related('from_user', 'to_user')
        
        colleagues = []
        for req in accepted:
            if req.from_user == self:
                colleagues.append(req.to_user)
            else:
                colleagues.append(req.from_user)
        return colleagues

    def is_colleague_with(self, other_user):
        """Проверяет, являются ли пользователи коллегами"""
        from django.db.models import Q
        return ColleagueRequest.objects.filter(
            Q(from_user=self, to_user=other_user) |
            Q(from_user=other_user, to_user=self),
            status='accepted'
        ).exists()

    def get_pending_request_to(self, other_user):
        """Возвращает исходящий запрос к другому пользователю, если есть"""
        return ColleagueRequest.objects.filter(
            from_user=self, to_user=other_user, status='pending'
        ).first()


class ColleagueRequest(models.Model):
    STATUS_CHOICES = [
        ('pending', 'Ожидает'),
        ('accepted', 'Принят'),
        ('rejected', 'Отклонён'),
    ]

    from_user = models.ForeignKey(
        User, on_delete=models.CASCADE,
        related_name='sent_colleague_requests',
        verbose_name='От пользователя'
    )
    to_user = models.ForeignKey(
        User, on_delete=models.CASCADE,
        related_name='received_colleague_requests',
        verbose_name='Кому'
    )
    status = models.CharField(
        max_length=10, choices=STATUS_CHOICES,
        default='pending', verbose_name='Статус'
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        unique_together = ['from_user', 'to_user']
        ordering = ['-created_at']
        verbose_name = 'Запрос в коллеги'
        verbose_name_plural = 'Запросы в коллеги'

    def __str__(self):
        return f"{self.from_user} → {self.to_user} ({self.get_status_display()})"