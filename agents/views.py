# agents/views.py
from django.contrib.auth.decorators import login_required
from django.shortcuts import render
from .models import Agent, Group, Manager
from django.shortcuts import redirect, get_object_or_404, render
from .forms import AgentForm
from datetime import datetime, timedelta
from django.contrib import messages

@login_required
def agent_list(request):
    agents = Agent.objects.all()
    return render(request, 'agent_list.html', {'agents': agents})

# @login_required
# def add_agent(request):
#     # context = {
#     #     'status_choices': Agent._meta.get_field('status').choices,
#     #     'groups': Group.objects.all()
#     # }
#     if request.method == 'POST':
#         form = AgentForm(request.POST, request.FILES)  # Fotoğraf için FILES eklenir
#         if form.is_valid():
#             form.save()
#             return redirect('agent_list')
#     else:
#         form = AgentForm()
#     return render(request, 'add_agent.html', {'form': form})

@login_required
def add_agent(request):    
    if request.method == 'POST':
        form = AgentForm(request.POST, request.FILES)
        if form.is_valid():
            form.save()
            messages.success(request, 'Personel başarıyla eklendi.')
            return redirect('agent_list')
        else:
            messages.error(request, 'Form doldurulurken bir hata oluştu. Lütfen tekrar deneyin.')
    else:
        form = AgentForm()

    context = {
        'form': form,
        'status_choices': Agent._meta.get_field('status').choices,
        'groups': Group.objects.all()
    }
    return render(request, 'add_agent.html', context)

def update_agent_status(request, pk):
    agent = get_object_or_404(Agent, pk=pk)
    if request.method == 'POST':
        status = request.POST.get('status')
        if status in dict(Agent.STATUS_CHOICES):  # Geçerli bir durum mu kontrol et
            agent.status = status
            agent.save()
            return redirect('agent_list')

    return render(request, 'update_status.html', {'agent': agent})

# Agent detalını redaktə etmək
# def edit_agent(request, agent_id):
#     agent = get_object_or_404(Agent, id=agent_id)
#     if request.method == 'POST':
#         form = AgentForm(request.POST, request.FILES, instance=agent)
#         if form.is_valid():
#             agent = form.save(commit=False)

#             # Status "Müsahibədən Keçdi" seçilirsə, qrupu soruş
#             if agent.status == "Passed to Training" or agent.status == "Invited to Work" or agent.status == "Failed to Work":
#                 manager_id = request.POST.get('manager')
#                 if manager_id:
#                     manager = get_object_or_404(Manager, id=manager_id)
#                     agent.manager = manager        
            
#             agent.save()
#             return redirect('agent_list')
#     else:
#         form = AgentForm(instance=agent)

#     managers = Manager.objects.all()
#     return render(request, 'edit_agent.html', {'form': form, 'agent': agent, 'managers': managers})

def edit_agent(request, agent_id):
    agent = get_object_or_404(Agent, id=agent_id)
    if request.method == 'POST':
        form = AgentForm(request.POST, request.FILES, instance=agent)
        if form.is_valid():
            agent = form.save(commit=False)
            
            # Status değişikliğine göre manager kontrolü
            if agent.status in ["Passed to Training", "Invited to Work", "Failed to Work"]:
                manager_id = request.POST.get('manager')
                if manager_id:
                    manager = get_object_or_404(Manager, id=manager_id)
                    agent.manager = manager
                else:
                    messages.error(request, 'Bu durum için yönetici seçimi zorunludur.')
                    return redirect('edit_agent', agent_id=agent_id)
            
            agent.save()
            messages.success(request, 'Personel başarıyla güncellendi.')
            return redirect('agent_list')
        else:
            messages.error(request, 'Form doldurulurken bir hata oluştu. Lütfen tekrar deneyin.')
    else:
        form = AgentForm(instance=agent)
        context = {
        'form': form,
        'agent': agent,
        'status_choices': Agent._meta.get_field('status').choices,
        'groups': Group.objects.all(),
        'managers': Manager.objects.all(),
    }
    return render(request, 'edit_agent.html', context)

def delete_agent(request, agent_id):
    """
    Personel silme view'i
    - Sadece POST isteklerini kabul eder
    - Silme işlemi öncesi nesnenin varlığını kontrol eder
    - İşlem sonrası kullanıcıya geri bildirim verir
    """
    if request.method == 'POST':
        agent = get_object_or_404(Agent, id=agent_id)
        agent_name = f"{agent.name} {agent.surname}"
        
        try:
            agent.delete()
            messages.success(
                request, 
                f'"{agent_name}" adlı personel başarıyla silindi.'
            )
        except Exception as e:
            messages.error(
                request, 
                'Personel silinirken bir hata oluştu. Lütfen tekrar deneyin.'
            )
        
    return redirect('agent_list')

def group_list(request):
    groups = Group.objects.all()  # Bütün qrupları gətir
    return render(request, 'groups/group_list.html', {'groups': groups})

def group_detail(request, group_id):
    group = get_object_or_404(Group, id=group_id)  # Seçilən qrupu tap
    agents = Agent.objects.filter(group=group)  # Qrupdakı agentləri gətir
    days = ['I', 'II', 'III', 'IV', 'V']
    
    # Cari həftənin başlanğıc və son tarixlərini hesablayaq
    today = datetime.now()
    monday = today - timedelta(days=today.weekday())  # Həftənin ilk günü
    friday = monday + timedelta(days=4)  # Həftənin son günü
    
    # Hər günün tarixini saxlayaq
    week_dates = [(monday + timedelta(days=i)).date() for i in range(5)]
    
    return render(request, 'groups/group_detail.html', {
        'group': group, 'agents': agents, 'days': days,
        'week_start': monday.date(),
        'week_end': friday.date(),
        'week_dates': week_dates,
        'current_date': today.date(),
        })

def manager_list(request):
    managers = Manager.objects.all()  # Bütün qrupları gətir
    return render(request, 'managers/manager_list.html', {'managers': managers})

def manager_detail(request, manager_id):
    manager = get_object_or_404(Manager, id=manager_id)  # Seçilən meneceri tap
    agents = Agent.objects.filter(manager=manager)  # Qrupdakı agentləri gətir
    return render(request, 'managers/manager_detail.html', {'manager': manager, 'agents': agents})

from .forms import ManagerForm
@login_required
def add_manager(request):
    if request.method == 'POST':
        form = ManagerForm(request.POST, request.FILES)
        if form.is_valid():
            form.save()
            messages.success(request, 'Yönetici başarıyla eklendi.')
            return redirect('manager_list')
        else:
            messages.error(request, 'Form doldurulurken bir hata oluştu. Lütfen tekrar deneyin.')
    else:
        form = ManagerForm()
    
    return render(request, 'managers/add_manager.html', {'form': form})

@login_required
def edit_manager(request, manager_id):
    manager = get_object_or_404(Manager, id=manager_id)
    
    if request.method == 'POST':
        form = ManagerForm(request.POST, request.FILES, instance=manager)
        if form.is_valid():
            form.save()
            messages.success(request, 'Yönetici bilgileri başarıyla güncellendi.')
            return redirect('manager_list')
        else:
            messages.error(request, 'Form doldurulurken bir hata oluştu. Lütfen tekrar deneyin.')
    else:
        form = ManagerForm(instance=manager)
    
    return render(request, 'managers/edit_manager.html', {
        'form': form,
        'manager': manager
    })

@login_required
def delete_manager(request, manager_id):
    manager = get_object_or_404(Manager, id=manager_id)
    
    if request.method == 'POST':
        # Yöneticiye bağlı personel varsa kontrol et
        if manager.agent_set.exists():
            messages.error(request, 'Bu yöneticiye bağlı personeller var. Önce personelleri başka bir yöneticiye aktarın.')
            return redirect('manager_list')
        
        try:
            manager_name = manager.name
            manager.delete()
            messages.success(request, f'"{manager_name}" adlı yönetici başarıyla silindi.')
        except Exception as e:
            messages.error(request, 'Yönetici silinirken bir hata oluştu. Lütfen tekrar deneyin.')
        
    return redirect('manager_list')