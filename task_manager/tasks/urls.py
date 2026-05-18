from django.urls import path
from . import views

app_name = 'tasks'

urlpatterns = [
    # Project URLs
    path('', views.project_list, name='project_list'),
    path('projects/<int:pk>/', views.project_detail, name='project_detail'),
    path('projects/create/', views.project_create, name='project_create'),
    path('projects/<int:pk>/edit/', views.project_edit, name='project_edit'),
    path('projects/<int:pk>/delete/', views.project_delete, name='project_delete'),
    
    # Task URLs
    path('tasks/create/<int:project_id>/', views.task_create, name='task_create'),
    path('tasks/<int:pk>/edit/', views.task_edit, name='task_edit'),
    path('tasks/<int:pk>/delete/', views.task_delete, name='task_delete'),
    path('tasks/<int:pk>/toggle-status/', views.task_toggle_status, name='task_toggle_status'),
    
    # Comment URLs
    path('comments/add/<int:task_id>/', views.comment_add, name='comment_add'),
    path('comments/<int:pk>/delete/', views.comment_delete, name='comment_delete'),
]