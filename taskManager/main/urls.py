from django.urls import path
from . import views

app_name = 'main'

urlpatterns = [
        path('', views.dashboard, name='dashboard'),
    
        # 📁 URLs для проектов
        path('projects/create/', views.project_create, name='project_create'),  # Создание проекта
        path('projects/<int:project_id>/', views.project_detail, name='project_detail'),  # Детали проекта
        path('projects/<int:project_id>/edit/', views.project_edit, name='project_edit'),  # Редактирование проекта
        #path('projects/', views.project_list, name='project_list'), # Список проектов
        
        # 👥 Управление участниками проектов
        # path('projects/<int:project_id>/invite/', views.invite_to_project, name='invite_to_project'),  # Приглашение в проект
        # path('projects/<int:project_id>/remove-member/<int:user_id>/', views.remove_from_project, name='remove_from_project'),  # Удаление участника
        
        # ✅ URLs для задач
        path('projects/<int:project_id>/tasks/create/', views.task_create, name='task_create'),  # Создание задачи
        path('tasks/<int:task_id>/edit/', views.task_edit, name='task_edit'),  # Редактирование задачи
        path('tasks/<int:task_id>/delete/', views.task_delete, name='task_delete'),  # Удаление задачи
        path('tasks/<int:task_id>/update-status/', views.update_task_status, name='update_task_status'),  # AJAX обновление статуса
]

