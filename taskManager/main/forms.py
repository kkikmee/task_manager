# forms.py
from django import forms
from .models import Project, Task, ProjectMembership
from django.contrib.auth import get_user_model

User = get_user_model()

class ProjectForm(forms.ModelForm):
    class Meta:
        model = Project
        fields = ['name', 'description', 'color']
        widgets = {
            'name': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Введите название проекта',
                'autofocus': True
            }),
            'description': forms.Textarea(attrs={
                'class': 'form-control',
                'placeholder': 'Опишите цели и задачи проекта...',
                'rows': 4
            }),
            'color': forms.TextInput(attrs={
                'class': 'form-control form-control-color',
                'type': 'color',
                'title': 'Выберите цвет проекта'
            }),
        }
        labels = {
            'name': 'Название проекта',
            'description': 'Описание',
            'color': 'Цвет проекта',
        }
        help_texts = {
            'name': 'Укажите понятное название проекта',
            'description': 'Опишите цели и задачи проекта',
            'color': 'Выберите цвет для визуального выделения',
        }

    def clean_name(self):
        name = self.cleaned_data.get('name')
        if name and len(name.strip()) < 2:
            raise forms.ValidationError("Название проекта должно содержать минимум 2 символа")
        return name.strip()

class TaskForm(forms.ModelForm):
    class Meta:
        model = Task
        fields = ['title', 'description', 'assigned_to', 'status', 'priority', 'due_date']
        widgets = {
            'title': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Введите название задачи'
            }),
            'description': forms.Textarea(attrs={
                'class': 'form-control',
                'placeholder': 'Опишите задачу...',
                'rows': 4
            }),
            'assigned_to': forms.Select(attrs={
                'class': 'form-select'
            }),
            'status': forms.Select(attrs={
                'class': 'form-select'
            }),
            'priority': forms.Select(attrs={
                'class': 'form-select'
            }),
            'due_date': forms.DateInput(attrs={
                'class': 'form-control',
                'type': 'date'
            }),
        }
        labels = {
            'title': 'Название задачи',
            'description': 'Описание',
            'assigned_to': 'Исполнитель',
            'status': 'Статус',
            'priority': 'Приоритет',
            'due_date': 'Срок выполнения',
        }

    def __init__(self, *args, **kwargs):
        self.project = kwargs.pop('project', None)
        super().__init__(*args, **kwargs)
        
        # Ограничиваем выбор исполнителей участниками проекта
        if self.project:
            self.fields['assigned_to'].queryset = self.project.team_members.all()
            # Добавляем пустое значение
            self.fields['assigned_to'].empty_label = "Не назначено"
        else:
            self.fields['assigned_to'].queryset = User.objects.filter(is_active=True)

class ProjectInviteForm(forms.Form):
    user = forms.ModelChoiceField(
        queryset=User.objects.filter(is_active=True),
        label="Пользователь",
        widget=forms.Select(attrs={'class': 'form-select'})
    )
    role = forms.ChoiceField(
        choices=ProjectMembership.ROLE_CHOICES,
        label="Роль в проекте",
        widget=forms.Select(attrs={'class': 'form-select'})
    )
    
    def __init__(self, *args, **kwargs):
        self.project = kwargs.pop('project', None)
        super().__init__(*args, **kwargs)
        
        # Исключаем пользователей, которые уже в проекте
        if self.project:
            existing_users = self.project.team_members.all()
            self.fields['user'].queryset = User.objects.filter(
                is_active=True
            ).exclude(id__in=existing_users.values_list('id', flat=True))
            
# forms.py
class ProjectForm(forms.ModelForm):
    class Meta:
        model = Project
        fields = ['name', 'description', 'color']
        widgets = {
            'name': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Например: Разработка веб-сайта компании',
                'autofocus': True,
                'maxlength': '100'
            }),
            'description': forms.Textarea(attrs={
                'class': 'form-control',
                'placeholder': 'Опишите цели, задачи и особенности проекта...',
                'rows': 5,
                'maxlength': '500'
            }),
            'color': forms.TextInput(attrs={
                'class': 'form-control-color',
                'type': 'color',
                'title': 'Выберите цвет проекта',
                'style': 'width: 60px; height: 40px; padding: 0; border: none;'
            }),
        }
        labels = {
            'name': 'Название проекта',
            'description': 'Описание проекта',
            'color': 'Цвет проекта',
        }
        help_texts = {
            'name': 'Укажите краткое и понятное название проекта',
            'description': 'Опишите цели и задачи проекта (максимум 500 символов)',
            'color': 'Выберите цвет для визуального выделения проекта',
        }

    def clean_name(self):
        name = self.cleaned_data.get('name')
        if name:
            name = name.strip()
            if len(name) < 2:
                raise forms.ValidationError("Название проекта должно содержать минимум 2 символа")
            if len(name) > 100:
                raise forms.ValidationError("Название проекта не должно превышать 100 символов")
        return name

    def clean_description(self):
        description = self.cleaned_data.get('description')
        if description and len(description) > 500:
            raise forms.ValidationError("Описание не должно превышать 500 символов")
        return description