from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.core.exceptions import PermissionDenied
from django.http import JsonResponse
from django.db import models
from django.db.models import Count, Q
from django.utils import timezone
from datetime import timedelta
from .models import Project, Task, ProjectMembership
from .forms import ProjectForm, TaskForm, ProjectInviteForm

def check_project_access(user, project):
    """
    Проверяет, имеет ли пользователь доступ к проекту.
    Вызывает PermissionDenied если доступ запрещен.
    """
    if not project.is_user_in_project(user):
        raise PermissionDenied("У вас нет доступа к этому проекту")

@login_required
def dashboard(request):
    """
    Главная страница - панель управления пользователя.
    Показывает обзор проектов и последние задачи.
    """
    # Получаем все проекты, где пользователь является создателем или участником
    projects = Project.objects.filter(
        Q(created_by=request.user) | 
        Q(team_members=request.user)
    ).distinct().select_related('created_by')
    
    # Получаем последние 5 задач из доступных проектов
    recent_tasks = Task.objects.filter(
        project__in=projects
    ).select_related('project', 'assigned_to', 'created_by').order_by('-created_at')[:5]
    
    # ПРАВИЛЬНЫЙ подсчет статистики
    total_tasks = 0
    total_done = 0
    total_in_progress = 0
    total_todo = 0
    
    # Собираем детальную статистику по каждому проекту
    projects_stats = []
    for project in projects:
        project_tasks = project.tasks.all()
        task_count = project_tasks.count()
        done_count = project_tasks.filter(status='done').count()
        in_progress_count = project_tasks.filter(status='in_progress').count()
        todo_count = project_tasks.filter(status='todo').count()
        
        # Общая статистика
        total_tasks += task_count
        total_done += done_count
        total_in_progress += in_progress_count
        total_todo += todo_count
        
        # Статистика для каждого проекта
        projects_stats.append({
            'project': project,
            'total': task_count,
            'done': done_count,
            'in_progress': in_progress_count,
            'todo': todo_count,
        })
    
    # Задачи назначенные на текущего пользователя
    my_tasks_count = Task.objects.filter(assigned_to=request.user).count()
    
    # Просроченные задачи (только активные, не выполненные)
    overdue_tasks = Task.objects.filter(
        project__in=projects,
        due_date__lt=timezone.now().date(),
        status__in=['todo', 'in_progress']
    ).count()
    
    # Задачи с высоким приоритетом
    high_priority_tasks = Task.objects.filter(
        project__in=projects,
        priority='high',
        status__in=['todo', 'in_progress']
    ).count()
    
    # Проекты с наибольшим количеством задач
    top_projects = projects.annotate(
        task_count=Count('tasks')
    ).order_by('-task_count')[:3]
    
    context = {
        'projects': projects,
        'recent_tasks': recent_tasks,
        'projects_stats': projects_stats,
        
        # Основная статистика
        'total_tasks': total_tasks,
        'total_done': total_done,
        'total_active': total_in_progress + total_todo,  # Активные = в работе + к выполнению
        'total_in_progress': total_in_progress,
        'total_todo': total_todo,
        'my_tasks_count': my_tasks_count,
        'overdue_tasks': overdue_tasks,
        'high_priority_tasks': high_priority_tasks,
        'today': timezone.now().date(),
        
        # Дополнительная информация
        'top_projects': top_projects,
    }
    
    return render(request, 'main/index/dashboard.html', context)

@login_required
def project_detail(request, project_id):
    """
    Детальная страница проекта со списком задач.
    Поддерживает фильтрацию и сортировку задач.
    """
    # Получаем проект или возвращаем 404
    project = get_object_or_404(Project, id=project_id)
    
    # Проверяем доступ пользователя к проекту
    check_project_access(request.user, project)
    
    # Получаем все задачи проекта с оптимизацией запросов
    tasks = project.tasks.all().select_related('assigned_to', 'created_by')
    
    project_tasks = project.tasks.all()
    task_count = project_tasks.count()
    done_count = project_tasks.filter(status='done').count()
    in_progress_count = project_tasks.filter(status='in_progress').count()
    
    
    # Фильтрация по статусу из GET-параметра
    status_filter = request.GET.get('status', '')
    if status_filter:
        tasks = tasks.filter(status=status_filter)
    
    # Фильтрация по исполнителю из GET-параметра
    assigned_filter = request.GET.get('assigned_to', '')
    if assigned_filter:
        tasks = tasks.filter(assigned_to_id=assigned_filter)
    
    # Сортировка из GET-параметра (по умолчанию - новые сначала)
    sort_by = request.GET.get('sort', '-created_at')
    if sort_by in ['title', 'status', 'priority', 'due_date', '-created_at']:
        tasks = tasks.order_by(sort_by)
    
    # Получаем участников проекта для фильтра по исполнителям
    available_assignees = project.team_members.all()
    
    # Получаем информацию о членах команды с их ролями
    team_members = project.get_team_members()
    
    context = {
        'project': project,
        'tasks': tasks,
        "task_count": task_count,
        "done_count": done_count,
        "progress_count": in_progress_count,
        'status_filter': status_filter,
        'assigned_filter': assigned_filter,
        'available_assignees': available_assignees,
        'team_members': team_members,
        'sort_by': sort_by,
    }
    return render(request, 'main/project/project_detail.html', context)

@login_required
def project_create(request):
    """
    Создание нового проекта.
    """
    if request.method == 'POST':
        form = ProjectForm(request.POST)
        if form.is_valid():
            # Создаем проект
            project = form.save(commit=False)
            project.created_by = request.user
            project.save()
            
            # Автоматически добавляем создателя в участники как менеджера
            ProjectMembership.objects.create(
                project=project,
                user=request.user,
                role='manager',
                can_edit_tasks=True,
                can_invite_users=True
            )
            
            messages.success(request, f'Проект "{project.name}" успешно создан!')
            return redirect('main:project_detail', project_id=project.id)
    else:
        # GET запрос - показываем пустую форму
        form = ProjectForm()
    
    return render(request, 'main/project/project_create.html', {'form': form, 'title': 'Создать проект'})

@login_required
def project_edit(request, project_id):
    """
    Редактирование существующего проекта.
    """
    project = get_object_or_404(Project, id=project_id)
    
    # Проверяем, что пользователь - создатель проекта
    if project.created_by != request.user:
        raise PermissionDenied("Только создатель может редактировать проект")
    
    # Вычисляем статистику
    total_tasks = project.tasks.count()
    done_tasks = project.tasks.filter(status='done').count()
    team_members_count = project.team_members.count() + 1  # + создатель
    
    if request.method == 'POST':
        form = ProjectForm(request.POST, instance=project)
        if form.is_valid():
            form.save()
            messages.success(request, f'Проект "{project.name}" успешно обновлен!')
            return redirect('project_detail', project_id=project.id)
    else:
        form = ProjectForm(instance=project)
    
    context = {
        'form': form, 
        'title': 'Редактировать проект',
        'project': project,
        'total_tasks': total_tasks,
        'done_tasks': done_tasks,
        'team_members_count': team_members_count,
    }
    return render(request, 'main/project/project_form.html', context)

@login_required
def task_create(request, project_id):
    """
    Создание новой задачи в проекте.
    """
    # Получаем проект и проверяем доступ
    project = get_object_or_404(Project, id=project_id)
    check_project_access(request.user, project)
    
    if request.method == 'POST':
        # Передаем проект в форму для ограничения исполнителей
        form = TaskForm(request.POST, project=project)
        if form.is_valid():
            # Создаем задачу, но не сохраняем сразу
            task = form.save(commit=False)
            # Устанавливаем проект и создателя
            task.project = project
            task.created_by = request.user
            # Сохраняем задачу в БД
            task.save()
            
            messages.success(request, f'Задача "{task.title}" создана!')
            return redirect('main:project_detail', project_id=project.id)
    else:
        # GET запрос - показываем пустую форму с предустановленными значениями
        initial_data = {
            'status': 'todo',
            'priority': 'medium',
        }
        form = TaskForm(initial=initial_data, project=project)
    
    return render(request, 'main/project/task_form.html', {
        'form': form, 
        'project': project,
        'title': 'Создать задачу'
    })

@login_required
def task_edit(request, task_id):
    """
    Редактирование существующей задачи.
    """
    # Получаем задачу и проверяем доступ к ее проекту
    task = get_object_or_404(Task, id=task_id)
    check_project_access(request.user, task.project)
    
    # Проверяем права на редактирование (только создатель или участник с правами)
    if task.created_by != request.user and not task.project.projectmembership_set.filter(
        user=request.user, can_edit_tasks=True
    ).exists():
        raise PermissionDenied("У вас нет прав для редактирования этой задачи")
    
    if request.method == 'POST':
        # Обновляем задачу данными из формы
        form = TaskForm(request.POST, instance=task, project=task.project)
        if form.is_valid():
            form.save()
            messages.success(request, f'Задача "{task.title}" обновлена!')
            return redirect('project_detail', project_id=task.project.id)
    else:
        # Показываем форму с текущими данными задачи
        form = TaskForm(instance=task, project=task.project)
    
    return render(request, 'main/project/task_form.html', {
        'form': form,
        'task': task,
        'project': task.project,
        'title': 'Редактировать задачу'
    })

# views.py
@login_required
def task_delete(request, task_id):
    """
    Удаление задачи.
    """
    # Получаем задачу и проверяем доступ
    task = get_object_or_404(Task, id=task_id)
    check_project_access(request.user, task.project)
    
    # Проверяем права на удаление (только создатель задачи или создатель проекта)
    if task.created_by != request.user and task.project.created_by != request.user:
        raise PermissionDenied("Только создатель задачи или создатель проекта может удалить задачу")
    
    if request.method == 'POST':
        # Удаляем задачу
        project_id = task.project.id
        task_title = task.title
        task.delete()
        
        messages.success(request, f'Задача "{task_title}" удалена!')
        return redirect('main:project_detail', project_id=project_id)
    
    # GET запрос - показываем страницу подтверждения
    context = {
        'task': task,
        'today': timezone.now().date(),
    }
    return render(request, 'main/project/task_confirm_delete.html', context)

@login_required
def update_task_status(request, task_id):
    """
    AJAX-функция для обновления статуса задачи.
    Работает без перезагрузки страницы.
    """
    # Проверяем, что это AJAX-запрос
    if request.method == 'POST' and request.headers.get('x-requested-with') == 'XMLHttpRequest':
        # Получаем задачу и проверяем доступ
        task = get_object_or_404(Task, id=task_id)
        check_project_access(request.user, task.project)
        
        # Получаем новый статус из POST-данных
        new_status = request.POST.get('status')
        
        # Проверяем, что статус допустимый
        if new_status in dict(Task.STATUS_CHOICES):
            # Обновляем статус и сохраняем
            task.status = new_status
            task.save()
            
            # Возвращаем JSON-ответ об успехе
            return JsonResponse({
                'success': True, 
                'new_status': task.get_status_display(),
                'status': task.status
            })
    
    # Если что-то пошло не так, возвращаем ошибку
    return JsonResponse({'success': False, 'error': 'Не удалось обновить статус'})

@login_required
def invite_to_project(request, project_id):
    """
    Приглашение нового участника в проект.
    Доступно только создателю и участникам с правами приглашения.
    """
    # Получаем проект
    project = get_object_or_404(Project, id=project_id)
    
    # Проверяем права на приглашение
    if project.created_by != request.user and not project.projectmembership_set.filter(
        user=request.user, can_invite_users=True
    ).exists():
        raise PermissionDenied("У вас нет прав для приглашения участников")
    
    if request.method == 'POST':
        # Обрабатываем форму приглашения
        form = ProjectInviteForm(request.POST)
        if form.is_valid():
            user = form.cleaned_data['user']
            role = form.cleaned_data['role']
            
            # Проверяем, не является ли пользователь уже участником
            if project.team_members.filter(id=user.id).exists():
                messages.error(request, f'Пользователь {user.username} уже в проекте!')
            else:
                # Создаем членство в проекте
                ProjectMembership.objects.create(
                    project=project,
                    user=user,
                    role=role
                )
                messages.success(request, f'Пользователь {user.username} приглашен в проект!')
                return redirect('project_detail', project_id=project.id)
    else:
        # GET запрос - показываем пустую форму
        form = ProjectInviteForm()
    
    return render(request, 'tasks/invite_form.html', {
        'form': form, 
        'project': project,
        'title': 'Пригласить в проект'
    })

@login_required
def remove_from_project(request, project_id, user_id):
    """
    Удаление участника из проекта.
    Доступно только создателю проекта.
    """
    # Получаем проект
    project = get_object_or_404(Project, id=project_id)
    
    # Проверяем, что пользователь - создатель проекта
    if project.created_by != request.user:
        raise PermissionDenied("Только создатель может удалять участников")
    
    # Получаем пользователя для удаления
    user_to_remove = get_object_or_404(project.team_members, id=user_id)
    
    if request.method == 'POST':
        # Удаляем членство в проекте
        ProjectMembership.objects.filter(project=project, user=user_to_remove).delete()
        messages.success(request, f'Пользователь {user_to_remove.username} удален из проекта!')
        return redirect('project_detail', project_id=project.id)
    
    # GET запрос - показываем страницу подтверждения
    return render(request, 'tasks/remove_member_confirm.html', {
        'project': project,
        'user_to_remove': user_to_remove
    })