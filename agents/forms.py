# agents/forms.py
from django import forms
from .models import Agent, Manager, Department

class AgentForm(forms.ModelForm):
    class Meta:
        model = Agent
        fields = ['photo', 'name', 'surname', 'fin', 'phone', 'status', 'group']

class ManagerForm(forms.ModelForm):
    class Meta:
        model = Manager
        fields = ['photo', 'name', 'surname']
        widgets = {
            'name': forms.TextInput(attrs={'class': 'form-control'}),
            'surname': forms.TextInput(attrs={'class': 'form-control'}),
        }

    def __init__(self, *args, department=None, **kwargs):
        super().__init__(*args, **kwargs)
        self.department = department

    def save(self, commit=True):
        manager = super().save(commit=False)
        if self.department:
            manager.department = self.department
        if commit:
            manager.save()
        return manager

class DepartmentForm(forms.ModelForm):
    class Meta:
        model = Department
        fields = ['name']
        widgets = {
            'name': forms.TextInput(attrs={'class': 'form-control'})
        }