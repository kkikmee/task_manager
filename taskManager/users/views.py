from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.shortcuts import render, get_object_or_404, redirect
from django.db.models import Count, Q
from django.utils import timezone
from main.models import Project, Task, ProjectMembership
from .forms import RegisterForm
from .models import User, ColleagueRequest


# ─────────────────────────── AUTH ───────────────────────────

def login_view(request):
    if request.method == 'POST':
        username = request.POST.get('username')
        password = request.POST.get('password')
        user = authenticate(request, username=username, password=password)
        if user is not None:
            login(request, user)
            next_url = request.POST.get('next') or 'main:dashboard'
            return redirect(next_url)
        else:
            messages.error(request, 'Неправильное имя пользователя или пароль')
    return render(request, 'users/login.html')


@login_required
def logout_view(request):
    logout(request)
    messages.success(request, 'Вы успешно вышли из системы')
    return redirect('users:login')


def register_view(request):
    if request.method == 'POST':
        form = RegisterForm(request.POST)
        if form.is_valid():
            user = form.save()
            login(request, user)
            messages.success(request, f'Добро пожаловать, {user.username}!')
            return redirect('main:dashboard')
    else:
        form = RegisterForm()
    return render(request, 'users/register.html', {'form': form})


# ─────────────────────────── PROJECTS / TASKS ───────────────────────────

@login_required
def project_list(request):
    projects = Project.objects.filter(
        Q(created_by=request.user) | Q(team_members=request.user)
    ).distinct().select_related('created_by')

    projects_with_stats = []
    for project in projects:
        task_count = project.tasks.count()
        team_count = project.team_members.count()
        done_count = project.tasks.filter(status='done').count()
        high_priority_count = project.tasks.filter(
            priority='high', status__in=['todo', 'in_progress']
        ).count()
        last_task = project.tasks.order_by('-updated_at').first()
        last_updated = last_task.updated_at if last_task else project.created_at

        project.task_count = task_count
        project.team_count = team_count
        project.done_count = done_count
        project.high_priority_count = high_priority_count
        project.last_updated = last_updated
        projects_with_stats.append(project)

    sort_by = request.GET.get('sort', '')
    sort_map = {
        'name': lambda x: x.name,
        '-name': (lambda x: x.name, True),
        '-created_at': (lambda x: x.created_at, True),
        'created_at': lambda x: x.created_at,
        '-task_count': (lambda x: x.task_count, True),
        'task_count': lambda x: x.task_count,
    }
    if sort_by in sort_map:
        val = sort_map[sort_by]
        if isinstance(val, tuple):
            projects_with_stats.sort(key=val[0], reverse=True)
        else:
            projects_with_stats.sort(key=val)
    else:
        projects_with_stats.sort(key=lambda x: x.created_at, reverse=True)

    return render(request, 'users/profile_projects.html', {'projects': projects_with_stats})


@login_required
def my_tasks(request):
    tasks = Task.objects.filter(
        assigned_to=request.user
    ).select_related('project', 'created_by').order_by('-created_at')

    status_filter = request.GET.get('status', '')
    if status_filter:
        tasks = tasks.filter(status=status_filter)

    sort_by = request.GET.get('sort', '')
    sort_map = {
        'due_date': 'due_date',
        '-due_date': '-due_date',
        '-created_at': '-created_at',
        'created_at': 'created_at',
        'priority': 'priority',
    }
    tasks = tasks.order_by(sort_map.get(sort_by, '-created_at'))

    projects = Project.objects.filter(
        Q(created_by=request.user) | Q(team_members=request.user)
    ).distinct()

    tasks_by_project = []
    project_ids = tasks.values_list('project_id', flat=True).distinct()
    for project in Project.objects.filter(id__in=project_ids):
        project_tasks = tasks.filter(project=project)
        if project_tasks.exists():
            tasks_by_project.append({
                'project': project,
                'tasks': list(project_tasks),
                'stats': {
                    'total': project_tasks.count(),
                    'done': project_tasks.filter(status='done').count(),
                    'in_progress': project_tasks.filter(status='in_progress').count(),
                    'todo': project_tasks.filter(status='todo').count(),
                }
            })
    tasks_by_project.sort(key=lambda x: x['stats']['total'], reverse=True)

    urgent_tasks = tasks.filter(priority='high', status__in=['todo', 'in_progress'])[:5]
    today = timezone.now().date()

    context = {
        'tasks_by_project': tasks_by_project,
        'urgent_tasks': urgent_tasks,
        'urgent_tasks_count': urgent_tasks.count(),
        'projects': projects,
        'status_filter': status_filter,
        'sort_by': sort_by,
        'today': today,
        'total_tasks': tasks.count(),
        'todo_count': tasks.filter(status='todo').count(),
        'in_progress_count': tasks.filter(status='in_progress').count(),
        'review_count': tasks.filter(status='review').count(),
        'done_count': tasks.filter(status='done').count(),
        'overdue_count': tasks.filter(due_date__lt=today, status__in=['todo', 'in_progress']).count(),
        'high_priority_count': tasks.filter(priority='high').count(),
        'medium_priority_count': tasks.filter(priority='medium').count(),
        'low_priority_count': tasks.filter(priority='low').count(),
    }
    return render(request, 'users/profile_tasks.html', context)


# ─────────────────────────── PROFILE ───────────────────────────

@login_required
def profile_view(request, username):
    """Профиль пользователя — видят все авторизованные."""
    profile_user = get_object_or_404(User, username=username)
    me = request.user

    # Статус коллегства
    is_colleague = me.is_colleague_with(profile_user)
    pending_sent = me.get_pending_request_to(profile_user)
    pending_received = ColleagueRequest.objects.filter(
        from_user=profile_user, to_user=me, status='pending'
    ).first()

    # Публичные проекты (только те, где profile_user — создатель или участник)
    user_projects = Project.objects.filter(
        Q(created_by=profile_user) | Q(team_members=profile_user)
    ).distinct().select_related('created_by')[:6]

    # Статистика задач
    task_stats = Task.objects.filter(assigned_to=profile_user).aggregate(
        total=Count('id'),
        done=Count('id', filter=Q(status='done')),
        in_progress=Count('id', filter=Q(status='in_progress')),
    )

    colleagues = profile_user.get_colleagues()

    context = {
        'profile_user': profile_user,
        'is_own_profile': me == profile_user,
        'is_colleague': is_colleague,
        'pending_sent': pending_sent,
        'pending_received': pending_received,
        'user_projects': user_projects,
        'task_stats': task_stats,
        'colleagues': colleagues[:8],
        'colleagues_count': len(colleagues),
    }
    return render(request, 'users/profile.html', context)


@login_required
def edit_profile(request):
    """Редактирование собственного профиля."""
    if request.method == 'POST':
        user = request.user
        user.first_name = request.POST.get('first_name', '').strip()
        user.last_name = request.POST.get('last_name', '').strip()
        user.bio = request.POST.get('bio', '').strip()
        if 'avatar' in request.FILES:
            user.avatar = request.FILES['avatar']
        user.save()
        messages.success(request, 'Профиль успешно обновлён!')
        return redirect('users:profile', username=user.username)
    return render(request, 'users/edit_profile.html', {'user': request.user})


# ─────────────────────────── COLLEAGUES ───────────────────────────

@login_required
def colleagues_list(request):
    """Мои коллеги + входящие запросы."""
    colleagues = request.user.get_colleagues()
    incoming = ColleagueRequest.objects.filter(
        to_user=request.user, status='pending'
    ).select_related('from_user')
    outgoing = ColleagueRequest.objects.filter(
        from_user=request.user, status='pending'
    ).select_related('to_user')

    context = {
        'colleagues': colleagues,
        'incoming': incoming,
        'outgoing': outgoing,
    }
    return render(request, 'users/colleagues.html', context)


@login_required
def send_colleague_request(request, user_id):
    """Отправить запрос в коллеги."""
    to_user = get_object_or_404(User, id=user_id)
    if to_user == request.user:
        messages.error(request, 'Нельзя добавить себя в коллеги')
        return redirect('users:profile', username=to_user.username)

    # Проверяем обратный запрос — если есть, сразу принимаем
    reverse_req = ColleagueRequest.objects.filter(
        from_user=to_user, to_user=request.user, status='pending'
    ).first()
    if reverse_req:
        reverse_req.status = 'accepted'
        reverse_req.save()
        messages.success(request, f'{to_user.username} добавлен в коллеги!')
        return redirect('users:profile', username=to_user.username)

    req, created = ColleagueRequest.objects.get_or_create(
        from_user=request.user,
        to_user=to_user,
        defaults={'status': 'pending'}
    )
    if created:
        messages.success(request, f'Запрос отправлен пользователю {to_user.username}')
    elif req.status == 'rejected':
        req.status = 'pending'
        req.save()
        messages.success(request, f'Запрос повторно отправлен {to_user.username}')
    else:
        messages.info(request, 'Запрос уже отправлен')

    return redirect('users:profile', username=to_user.username)


@login_required
def accept_colleague_request(request, request_id):
    """Принять запрос в коллеги."""
    req = get_object_or_404(ColleagueRequest, id=request_id, to_user=request.user)
    req.status = 'accepted'
    req.save()
    messages.success(request, f'{req.from_user.username} теперь ваш коллега!')
    return redirect('users:colleagues')


@login_required
def reject_colleague_request(request, request_id):
    """Отклонить запрос в коллеги."""
    req = get_object_or_404(ColleagueRequest, id=request_id, to_user=request.user)
    req.status = 'rejected'
    req.save()
    messages.info(request, f'Запрос от {req.from_user.username} отклонён')
    return redirect('users:colleagues')


@login_required
def remove_colleague(request, user_id):
    """Удалить из коллег."""
    other = get_object_or_404(User, id=user_id)
    ColleagueRequest.objects.filter(
        Q(from_user=request.user, to_user=other) |
        Q(from_user=other, to_user=request.user)
    ).delete()
    messages.success(request, f'{other.username} удалён из коллег')
    return redirect('users:colleagues')


# ─────────────────────────── SEARCH ───────────────────────────

@login_required
def search_users(request):
    """Поиск пользователей по username / имени."""
    query = request.GET.get('q', '').strip()
    results = []
    if query:
        results = User.objects.filter(
            Q(username__icontains=query) |
            Q(first_name__icontains=query) |
            Q(last_name__icontains=query)
        ).exclude(id=request.user.id)[:20]

    # Для каждого результата определяем статус
    enriched = []
    for u in results:
        is_colleague = request.user.is_colleague_with(u)
        pending_sent = request.user.get_pending_request_to(u)
        pending_received = ColleagueRequest.objects.filter(
            from_user=u, to_user=request.user, status='pending'
        ).first()
        enriched.append({
            'user': u,
            'is_colleague': is_colleague,
            'pending_sent': pending_sent,
            'pending_received': pending_received,
        })

    return render(request, 'users/search.html', {
        'query': query,
        'results': enriched,
    })


# ─────────────────────────── INVITE TO PROJECT ───────────────────────────

@login_required
def invite_to_project(request, project_id):
    """
    Приглашение коллеги в проект.
    Доступно создателю и участникам с правами can_invite_users.
    """
    from main.models import Project, ProjectMembership
    project = get_object_or_404(Project, id=project_id)

    # Проверка прав
    can_invite = (
        project.created_by == request.user or
        project.projectmembership_set.filter(user=request.user, can_invite_users=True).exists()
    )
    if not can_invite:
        from django.core.exceptions import PermissionDenied
        raise PermissionDenied("У вас нет прав для приглашения участников")

    # Коллеги, которых ещё нет в проекте
    all_colleagues = request.user.get_colleagues()
    existing_ids = set(project.team_members.values_list('id', flat=True))
    existing_ids.add(project.created_by.id)
    available_colleagues = [u for u in all_colleagues if u.id not in existing_ids]

    if request.method == 'POST':
        user_id = request.POST.get('user_id')
        role = request.POST.get('role', 'developer')

        invited_user = get_object_or_404(User, id=user_id)

        # Проверяем: пользователь должен быть коллегой
        if not request.user.is_colleague_with(invited_user) and project.created_by != request.user:
            messages.error(request, 'Можно приглашать только коллег')
            return redirect('main:invite_to_project', project_id=project_id)

        if project.team_members.filter(id=invited_user.id).exists():
            messages.error(request, f'{invited_user.username} уже в проекте!')
        else:
            ProjectMembership.objects.create(
                project=project,
                user=invited_user,
                role=role
            )
            messages.success(request, f'{invited_user.username} добавлен в проект!')
            return redirect('main:project_detail', project_id=project.id)

    role_choices = ProjectMembership.ROLE_CHOICES
    return render(request, 'users/invite_to_project.html', {
        'project': project,
        'available_colleagues': available_colleagues,
        'role_choices': role_choices,
    })