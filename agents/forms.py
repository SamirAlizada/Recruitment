# agents/forms.py
from django import forms
from .models import Agent, Manager

class AgentForm(forms.ModelForm):
    class Meta:
        model = Agent
        fields = ['photo', 'name', 'surname', 'fin', 'status', 'group']

class ManagerForm(forms.ModelForm):
    class Meta:
        model = Manager
        fields = ['name', 'surname', 'department']
