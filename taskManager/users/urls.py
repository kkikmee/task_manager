from django.urls import path
from . import views

app_name = 'users'

urlpatterns = [
    # Auth
    path('login/', views.login_view, name='login'),
    path('logout/', views.logout_view, name='logout'),
    path('register/', views.register_view, name='register'),

    # Projects / Tasks
    path('projects/', views.project_list, name='project_list'),
    path('my-tasks/', views.my_tasks, name='my_tasks'),

    # Profile
    path('profile/<str:username>/', views.profile_view, name='profile'),
    path('profile/edit/me/', views.edit_profile, name='edit_profile'),

    # Colleagues
    path('colleagues/', views.colleagues_list, name='colleagues'),
    path('colleagues/send/<int:user_id>/', views.send_colleague_request, name='send_colleague_request'),
    path('colleagues/accept/<int:request_id>/', views.accept_colleague_request, name='accept_colleague_request'),
    path('colleagues/reject/<int:request_id>/', views.reject_colleague_request, name='reject_colleague_request'),
    path('colleagues/remove/<int:user_id>/', views.remove_colleague, name='remove_colleague'),

    # Search
    path('search/', views.search_users, name='search_users'),

    # Invite (override main's invite)
    path('projects/<int:project_id>/invite/', views.invite_to_project, name='invite_to_project'),
]