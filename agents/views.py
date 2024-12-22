# agents/views.py
from django.contrib.auth.decorators import login_required
from django.shortcuts import render
from .models import Agent, Group, Manager
from django.shortcuts import redirect, get_object_or_404, render
from .forms import AgentForm
from datetime import datetime, timedelta

@login_required
def agent_list(request):
    agents = Agent.objects.all()
    return render(request, 'agent_list.html', {'agents': agents})

@login_required
def add_agent(request):
    if request.method == 'POST':
        form = AgentForm(request.POST, request.FILES)  # Fotoğraf için FILES eklenir
        if form.is_valid():
            form.save()
            return redirect('agent_list')
    else:
        form = AgentForm()
    return render(request, 'add_agent.html', {'form': form})


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
def edit_agent(request, agent_id):
    agent = get_object_or_404(Agent, id=agent_id)
    if request.method == 'POST':
        form = AgentForm(request.POST, request.FILES, instance=agent)
        if form.is_valid():
            agent = form.save(commit=False)

            # Status "Müsahibədən Keçdi" seçilirsə, qrupu soruş
            if agent.status == "Passed to Training" or agent.status == "Invited to Work" or agent.status == "Failed to Work":
                manager_id = request.POST.get('manager')
                if manager_id:
                    manager = get_object_or_404(Manager, id=manager_id)
                    agent.manager = manager        
            
            agent.save()
            return redirect('agent_list')
    else:
        form = AgentForm(instance=agent)

    managers = Manager.objects.all()
    return render(request, 'edit_agent.html', {'form': form, 'agent': agent, 'managers': managers})

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