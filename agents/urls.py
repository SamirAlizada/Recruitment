# agents/urls.py
from django.urls import path
from . import views

urlpatterns = [
    path('', views.agent_list, name='agent_list'),
    path('add/', views.add_agent, name='add_agent'),
    path('update/<int:pk>/', views.update_agent_status, name='update_agent_status'),
    path('edit/<int:pk>/', views.edit_agent, name='edit_agent'),
    path('agent/<int:pk>/delete/', views.agent_delete, name='agent_delete'),
    path('agents/<int:agent_id>/delete/', views.delete_agent, name='delete_agent'),
    
    path('groups/', views.group_list, name='group_list'),
    path('groups/<int:group_id>/', views.group_detail, name='group_detail'),

    path('managers/', views.manager_list, name='manager_list'),
    path('managers/<int:manager_id>/', views.manager_detail, name='manager_detail'),
    path('managers/', views.manager_list, name='manager_list'),
    path('managers/add/', views.add_manager, name='add_manager'),
    path('managers/<int:manager_id>/edit/', views.edit_manager, name='edit_manager'),
    path('managers/<int:manager_id>/delete/', views.delete_manager, name='delete_manager'),

    path('departments/', views.department_list, name='department_list'),
    path('departments/add/', views.add_department, name='add_department'),
    path('departments/<int:pk>/edit/', views.edit_department, name='edit_department'),
    path('departments/<int:pk>/delete/', views.delete_department, name='delete_department'),
    path('departments/<int:pk>/', views.department_detail, name='department_detail'),
    path('departments/<int:dept_pk>/managers/<int:manager_pk>/edit/', views.edit_manager, name='edit_manager'),
    path('departments/<int:dept_pk>/managers/<int:manager_pk>/delete/', views.delete_manager, name='delete_manager'),
    path('departments/<int:dept_pk>/managers/<int:manager_pk>/', views.manager_detail, name='manager_detail'),
    path('api/departments/<int:dept_id>/managers/', views.get_department_managers, name='get_department_managers'),
    path('departments/<int:dept_pk>/add-manager/', views.add_manager, name='department_add_manager'),
    path('update-agent-values/', views.update_agent_values, name='update_agent_values'),
]
