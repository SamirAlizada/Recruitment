# agents/urls.py
from django.urls import path
from . import views

urlpatterns = [
    path('', views.agent_list, name='agent_list'),
    path('add/', views.add_agent, name='add_agent'),
    path('update/<int:pk>/', views.update_agent_status, name='update_agent_status'),
    path('edit/<int:agent_id>/', views.edit_agent, name='edit_agent'),

    path('groups/', views.group_list, name='group_list'),
    path('groups/<int:group_id>/', views.group_detail, name='group_detail'),

    path('managers/', views.manager_list, name='manager_list'),
    path('managers/<int:manager_id>/', views.manager_detail, name='manager_detail'),
]