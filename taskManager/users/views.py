from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from django.db.models import Count, Q, Max
from django.db import models
from main.models import Project, Task
from django.utils import timezone

def login_view(request):
    """
    Страница входа пользователя.
    """
    if request.method == 'POST':
        username = request.POST.get('username')
        password = request.POST.get('password')
        user = authenticate(request, username=username, password=password)
        
        if user is not None:
            login(request, user)
            
            # Перенаправляем на next или dashboard
            next_url = request.POST.get('next', 'main:dashboard')
            if next_url:
                return redirect(next_url)
            return redirect('main:dashboard')
        else:
            messages.error(request, 'Неправильное имя пользователя или пароль')
    
    return render(request, 'users/login.html')

@login_required
def logout_view(request):
    """
    Выход пользователя.
    """
    logout(request)
    messages.success(request, 'Вы успешно вышли из системы')
    return redirect('users:login')


def register_view(request):
    """
    Страница регистрации пользователя.
    """
    if request.method == 'POST':
        form = UserCreationForm(request.POST)
        if form.is_valid():
            user = form.save()
            
            # Автоматический вход после регистрации
            login(request, user)
            messages.success(request, f'Добро пожаловать, {user.username}!')
            return redirect('main:dashboard')
    else:
        form = UserCreationForm()
    
    return render(request, 'users/register.html', {'form': form})

@login_required
def project_list(request):
    """
    Страница со списком всех проектов пользователя.
    """
    projects = Project.objects.filter(
        Q(created_by=request.user) | 
        Q(team_members=request.user)
    ).distinct().select_related('created_by')
    
    projects_with_stats = []
    for project in projects:
        # Количество задач
        task_count = project.tasks.count()
        
        # Количество участников (без создателя)
        team_count = project.team_members.count()
        
        # Количество выполненных задач
        done_count = project.tasks.filter(status='done').count()
        
        # Количество задач с высоким приоритетом
        high_priority_count = project.tasks.filter(
            priority='high', 
            status__in=['todo', 'in_progress']
        ).count()
        
        # Дата последнего обновления
        last_task = project.tasks.order_by('-updated_at').first()
        last_updated = last_task.updated_at if last_task else project.created_at
        
        # Добавляем вычисленные поля к проекту
        project.task_count = task_count
        project.team_count = team_count
        project.done_count = done_count
        project.high_priority_count = high_priority_count
        project.last_updated = last_updated
        
        projects_with_stats.append(project)
    
    # Сортировка
    sort_by = request.GET.get('sort', '')
    if sort_by == 'name':
        projects_with_stats.sort(key=lambda x: x.name)
    elif sort_by == '-name':
        projects_with_stats.sort(key=lambda x: x.name, reverse=True)
    elif sort_by == '-created_at':
        projects_with_stats.sort(key=lambda x: x.created_at, reverse=True)
    elif sort_by == 'created_at':
        projects_with_stats.sort(key=lambda x: x.created_at)
    elif sort_by == '-task_count':
        projects_with_stats.sort(key=lambda x: x.task_count, reverse=True)
    elif sort_by == 'task_count':
        projects_with_stats.sort(key=lambda x: x.task_count)
    else:
        projects_with_stats.sort(key=lambda x: x.created_at, reverse=True)
    
    context = {
        'projects': projects_with_stats,
    }
    return render(request, 'users/profile_projects.html', context)

# views.py
# views.py
@login_required
def my_tasks(request):
    """
    Страница с задачами, назначенными на текущего пользователя.
    """
    # Задачи, где пользователь является исполнителем
    tasks = Task.objects.filter(
        assigned_to=request.user
    ).select_related('project', 'created_by').order_by('-created_at')
    
    # Фильтрация по статусу
    status_filter = request.GET.get('status', '')
    if status_filter:
        tasks = tasks.filter(status=status_filter)
    
    # Сортировка
    sort_by = request.GET.get('sort', '')
    if sort_by == 'due_date':
        tasks = tasks.order_by('due_date')
    elif sort_by == '-due_date':
        tasks = tasks.order_by('-due_date')
    elif sort_by == '-created_at':
        tasks = tasks.order_by('-created_at')
    elif sort_by == 'created_at':
        tasks = tasks.order_by('created_at')
    elif sort_by == 'priority':
        tasks = tasks.order_by('priority')
    else:
        tasks = tasks.order_by('-created_at')
    
    # Получаем проекты пользователя для быстрого создания задач
    projects = Project.objects.filter(
        Q(created_by=request.user) | 
        Q(team_members=request.user)
    ).distinct()
    
    # Группируем задачи по проектам - ИСПРАВЛЕННЫЙ КОД
    tasks_by_project = []
    
    # Получаем все проекты, где есть задачи пользователя
    project_ids = tasks.values_list('project_id', flat=True).distinct()
    user_projects = Project.objects.filter(id__in=project_ids)
    
    for project in user_projects:
        project_tasks = tasks.filter(project=project)
        if project_tasks.exists():  # Проверяем, что есть задачи в проекте
            tasks_by_project.append({
                'project': project,
                'tasks': list(project_tasks),  # Преобразуем в список
                'stats': {
                    'total': project_tasks.count(),
                    'done': project_tasks.filter(status='done').count(),
                    'in_progress': project_tasks.filter(status='in_progress').count(),
                    'todo': project_tasks.filter(status='todo').count(),
                }
            })
    
    # Сортируем проекты по количеству задач (больше задач сначала)
    tasks_by_project.sort(key=lambda x: x['stats']['total'], reverse=True)
    
    # Срочные задачи (высокий приоритет и не выполнены)
    urgent_tasks = tasks.filter(
        priority='high',
        status__in=['todo', 'in_progress']
    )[:5]  # Ограничиваем 5 задачами
    
    # Статистика
    total_tasks = tasks.count()
    todo_count = tasks.filter(status='todo').count()
    in_progress_count = tasks.filter(status='in_progress').count()
    review_count = tasks.filter(status='review').count()
    done_count = tasks.filter(status='done').count()
    overdue_count = tasks.filter(
        due_date__lt=timezone.now().date(),
        status__in=['todo', 'in_progress']
    ).count()
    
    # Статистика по приоритетам
    high_priority_count = tasks.filter(priority='high').count()
    medium_priority_count = tasks.filter(priority='medium').count()
    low_priority_count = tasks.filter(priority='low').count()
    
    context = {
        'tasks_by_project': tasks_by_project,  # Теперь точно передается
        'urgent_tasks': urgent_tasks,
        'urgent_tasks_count': urgent_tasks.count(),
        'projects': projects,
        'status_filter': status_filter,
        'sort_by': sort_by,
        'today': timezone.now().date(),
        
        # Статистика
        'total_tasks': total_tasks,
        'todo_count': todo_count,
        'in_progress_count': in_progress_count,
        'review_count': review_count,
        'done_count': done_count,
        'overdue_count': overdue_count,
        
        # Статистика по приоритетам
        'high_priority_count': high_priority_count,
        'medium_priority_count': medium_priority_count,
        'low_priority_count': low_priority_count,
    }
    return render(request, 'users/profile_tasks.html', context)