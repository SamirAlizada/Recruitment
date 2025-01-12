# agents/forms.py
from django import forms
from .models import Agent, Manager, Department, DepartmentHead, Group
from django.contrib.auth.models import User
import random
import string

class AgentForm(forms.ModelForm):
    # group = forms.ModelChoiceField(
    #     queryset=Group.objects.all(),
    #     widget=forms.Select(attrs={'class': 'form-control'}),
    #     required=False,
    #     empty_label="-----"
    # )

    class Meta:
        model = Agent
        fields = ['photo', 'name', 'surname', 'fin', 'phone', 'status', 'group']
        labels = {
            'name': 'Ad',
            'surname': 'Soyad',
            'fin': 'Fin',
            'phone': 'Telefon',
            'status': 'Status',
            'group': 'Qrup',
        }
        widgets = {
            'name': forms.TextInput(attrs={'class': 'form-control'}),
            'surname': forms.TextInput(attrs={'class': 'form-control'}),
            'fin': forms.TextInput(attrs={'class': 'form-control'}),
            'phone': forms.TextInput(attrs={'class': 'form-control'}),
            'status': forms.Select(attrs={'class': 'form-control'}),
            'photo': forms.FileInput(attrs={'class': 'form-control'}),
        }

        def __init__(self, *args, **kwargs):
            super(AgentForm, self).__init__(*args, **kwargs)
            self.fields['group'].queryset = Group.objects.all()  # Dinamik olarak ayarla

class ManagerForm(forms.ModelForm):
    password = forms.CharField(widget=forms.PasswordInput(attrs={'class': 'form-control'}), required=True)
    confirm_password = forms.CharField(widget=forms.PasswordInput(attrs={'class': 'form-control'}), required=True)
    photo = forms.ImageField(
        required=False,
        widget=forms.FileInput(attrs={
            'class': 'form-control d-none',
            'accept': 'image/*'
        })
    )

    class Meta:
        model = Manager
        fields = ['photo', 'name', 'surname']
        labels = {
            'name': 'Ad',
            'surname': 'Soyad',
        }
        widgets = {
            'name': forms.TextInput(attrs={'class': 'form-control'}),
            'surname': forms.TextInput(attrs={'class': 'form-control'}),
        }

    def __init__(self, *args, department=None, **kwargs):
        super().__init__(*args, **kwargs)
        self.department = department

    def clean(self):
        cleaned_data = super().clean()
        password = cleaned_data.get('password')
        confirm_password = cleaned_data.get('confirm_password')

        if password and confirm_password and password != confirm_password:
            raise forms.ValidationError('Şifrələr uyğun gəlmir!')

        if not self.department:
            raise forms.ValidationError('Şöbə məlumatı yoxdur!')

        return cleaned_data

    def save(self, commit=True):
        manager = super().save(commit=False)
        manager.department = self.department

        if commit:
            # Önce manager'ı kaydet
            manager.save()

            # Kullanıcı adını oluştur (isim.soyisim formatında)
            username = f"{manager.name.lower()}.{manager.surname.lower()}"
            
            # Eğer bu kullanıcı adı zaten varsa, sonuna numara ekle
            base_username = username
            counter = 1
            while User.objects.filter(username=username).exists():
                username = f"{base_username}{counter}"
                counter += 1

            # Yeni user oluştur
            user = User.objects.create_user(
                username=username,
                password=self.cleaned_data['password']
            )
            
            # Manager ile user'ı ilişkilendir
            manager.user = user
            manager.save()

        return manager

class DepartmentForm(forms.ModelForm):
    class Meta:
        model = Department
        fields = ['name']
        labels = {
            'name': 'Ad',
        }
        widgets = {
            'name': forms.TextInput(attrs={'class': 'form-control'})
        }

class DepartmentHeadForm(forms.ModelForm):
    password = forms.CharField(
        widget=forms.PasswordInput(attrs={'class': 'form-control'}),
        required=False,
        label='Şifrə'
    )
    confirm_password = forms.CharField(
        widget=forms.PasswordInput(attrs={'class': 'form-control'}),
        required=False,
        label='Şifrəni təsdiqlə'
    )
    photo = forms.ImageField(
        required=False,
        widget=forms.FileInput(attrs={
            'class': 'form-control d-none',
            'accept': 'image/*'
        })
    )

    class Meta:
        model = DepartmentHead
        fields = ['photo', 'name', 'surname', 'department']
        labels = {
            'name': 'Ad',
            'surname': 'Soyad',
            'department': 'Şöbə',
        }
        widgets = {
            'name': forms.TextInput(attrs={'class': 'form-control'}),
            'surname': forms.TextInput(attrs={'class': 'form-control'}),
            'department': forms.Select(attrs={'class': 'form-control'}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        if self.instance and self.instance.pk:
            # Edit mode - remove password fields
            if 'password' in self.fields:
                del self.fields['password']
            if 'confirm_password' in self.fields:
                del self.fields['confirm_password']
        else:
            # Add mode - make password fields required
            if 'password' in self.fields:
                self.fields['password'].required = True
            if 'confirm_password' in self.fields:
                self.fields['confirm_password'].required = True

    def clean(self):
        cleaned_data = super().clean()
        password = cleaned_data.get('password')
        confirm_password = cleaned_data.get('confirm_password')

        if not self.instance.pk:  # Only for new department heads
            if password != confirm_password:
                raise forms.ValidationError('Şifrələr uyğun gəlmir.')

        return cleaned_data

    def save(self, commit=True):
        department_head = super().save(commit=False)
        
        if not department_head.pk:
            # Only for new department heads
            username = f"{department_head.name.lower()}.{department_head.surname.lower()}"
            
            base_username = username
            counter = 1
            while User.objects.filter(username=username).exists():
                username = f"{base_username}{counter}"
                counter += 1
            
            user = User.objects.create_user(
                username=username,
                password=self.cleaned_data['password']
            )
            
            department_head.user = user
            self.cleaned_data['username'] = username

        if commit:
            department_head.save()
        
        return department_head

class GroupForm(forms.ModelForm):
    class Meta:
        model = Group
        fields = ['name']
        widgets = {
            'name': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Qrup adı'})
        }