# agents/forms.py
from django import forms
from .models import Agent

class AgentForm(forms.ModelForm):
    class Meta:
        model = Agent
        fields = ['photo', 'name', 'surname', 'fin', 'status', 'group']
