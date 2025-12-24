from django.urls import path
from . import views

app_name = 'users'

urlpatterns = [
    path('login/', views.login_view, name='login'),
    path('logout/', views.logout_view, name='logout'),
    path('register/', views.register_view, name='register'),
    
    path('projects/', views.project_list, name='project_list'),
    path('my-tasks/', views.my_tasks, name='my_tasks'),
]