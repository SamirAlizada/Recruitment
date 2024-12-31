# agents/views.py
from django.contrib.auth.decorators import login_required, user_passes_test
from django.shortcuts import render
from .models import Agent, Group, Manager, Department, AgentSchedule
from django.shortcuts import redirect, get_object_or_404, render
from .forms import AgentForm, DepartmentForm, ManagerForm
from datetime import datetime, timedelta
from django.contrib import messages
from django.http import JsonResponse
from django import forms
import logging
from django.contrib.auth.models import User
from django.core.exceptions import PermissionDenied
from django.contrib.auth import authenticate, login

def is_superuser(user):
    return user.is_superuser

# Logging yapılandırması
logger = logging.getLogger(__name__)

from django import template
from datetime import datetime

register = template.Library()

@register.filter
def az_month(value):
    az_months = {
        'January': 'Yanvar',
        'February': 'Fevral',
        'March': 'Mart',
        'April': 'Aprel',
        'May': 'May',
        'June': 'İyun',
        'July': 'İyul',
        'August': 'Avqust',
        'September': 'Sentyabr',
        'October': 'Oktyabr',
        'November': 'Noyabr',
        'December': 'Dekabr'
    }
    
    if isinstance(value, datetime):
        month = value.strftime('%B')
        year = value.strftime('%Y')
        return f"{az_months.get(month, month)} {year}"
    
    # Eğer string ise (regroup ile gelen değer için)
    for eng, az in az_months.items():
        if eng in value:
            return value.replace(eng, az)
    return value

@login_required
@user_passes_test(is_superuser)
def agent_list(request):
    agents = Agent.objects.all().order_by('-created_at')
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

# @login_required
# @user_passes_test(is_superuser)
# def add_agent(request):    
#     if request.method == 'POST':
#         form = AgentForm(request.POST, request.FILES)
#         if form.is_valid():
#             form.save()
#             messages.success(request, 'Personel başarıyla eklendi.')
#             return redirect('agent_list')
#         else:
#             messages.error(request, 'Form doldurulurken bir hata oluştu. Lütfen tekrar deneyin.')
#     else:
#         form = AgentForm()

#     context = {
#         'form': form,
#         'status_choices': Agent._meta.get_field('status').choices,
#         'groups': Group.objects.all()
#     }
#     return render(request, 'add_agent.html', context)


@login_required
@user_passes_test(is_superuser)
def add_agent(request):    
    if request.method == 'POST':
        form = AgentForm(request.POST, request.FILES)
        if form.is_valid():
            form.save()
            messages.success(request, 'Personel başarıyla eklendi.')
            return redirect('agent_list')
        else:
            messages.error(request, 'Form doldurulurken bir hata oluştu. Lütfen tekrar deneyin.')
            print(form.errors)  # Hata mesajlarını yazdır
            print(request.POST)  # Gönderilen verileri yazdır
            group_id = request.POST.get('group')
            print(f"Group ID Sent: {group_id}")  # Gönderilen grup ID'si
            print(f"Available Groups: {[group.id for group in Group.objects.all()]}")  # Mevcut gruplar kontrolü
    else:
        form = AgentForm()

    groups = Group.objects.all()

    context = {
        'form': form,
        'status_choices': Agent._meta.get_field('status').choices,
        'groups': groups,
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

def get_department_managers(request, dept_id):
    logger.debug(f"get_department_managers çağrıldı. dept_id: {dept_id}")
    
    try:
        department = get_object_or_404(Department, id=dept_id)
        logger.debug(f"Departman bulundu: {department.name}")
        
        managers = Manager.objects.filter(department=department)
        logger.debug(f"Bulunan yönetici sayısı: {managers.count()}")
        
        manager_list = []
        for manager in managers:
            manager_data = {
                'id': manager.id,
                'name': manager.name,
                'surname': manager.surname
            }
            manager_list.append(manager_data)
            logger.debug(f"Yönetici eklendi: {manager_data}")
        
        logger.debug(f"Dönülen manager listesi: {manager_list}")
        return JsonResponse(manager_list, safe=False)
        
    except Department.DoesNotExist:
        logger.error(f"Departman bulunamadı: {dept_id}")
        return JsonResponse({'error': 'Departman bulunamadı'}, status=404)
    except Exception as e:
        logger.error(f"Beklenmeyen hata: {str(e)}")
        return JsonResponse({'error': str(e)}, status=500)

def edit_agent(request, pk):
    agent = get_object_or_404(Agent, pk=pk)
    departments = Department.objects.all()
    managers = Manager.objects.all()
    referer_url = request.META.get('HTTP_REFERER')  # Önceki sayfanın URL'ini al
    
    if request.method == 'POST':
        form = AgentForm(request.POST, request.FILES, instance=agent)
        if form.is_valid():
            agent = form.save(commit=False)
            
            if agent.status in ['Passed to Training', 'Invited to Work', 'Failed to Work']:
                department_id = request.POST.get('department')
                manager_id = request.POST.get('manager')
                
                if department_id and manager_id:
                    selected_manager = get_object_or_404(Manager, id=manager_id, department_id=department_id)
                    agent.manager = selected_manager
                else:
                    form.add_error(None, 'Bu status için departman ve yönetici seçimi zorunludur.')
                    return render(request, 'agents/edit_agent.html', {
                        'form': form,
                        'agent': agent,
                        'departments': departments,
                        'managers': managers,
                        'status_choices': Agent._meta.get_field('status').choices,
                        'groups': Group.objects.all(),
                        'title': 'Agent Düzenle'
                    })
            else:
                agent.manager = None
            
            agent.save()
            messages.success(request, 'Agent başarıyla güncellendi.')
            
            # Form gönderildiğinde session'da saklanan referer URL'e yönlendir
            previous_url = request.session.get('previous_url')
            if previous_url:
                del request.session['previous_url']  # URL'i kullandıktan sonra sil
                return redirect(previous_url)
            
            # Eğer session'da URL yoksa varsayılan yönlendirme
            if agent.manager:
                return redirect('manager_detail', dept_pk=agent.manager.department.id, manager_pk=agent.manager.id)
            elif agent.group:
                return redirect('group_detail', group_id=agent.group.id)
            else:
                return redirect('agent_list')
    else:
        form = AgentForm(instance=agent)
        # GET isteğinde referer URL'i session'a kaydet
        if referer_url and '/edit/' not in referer_url:
            request.session['previous_url'] = referer_url
    
    return render(request, 'agents/edit_agent.html', {
        'form': form,
        'agent': agent,
        'departments': departments,
        'managers': managers,
        'status_choices': Agent._meta.get_field('status').choices,
        'groups': Group.objects.all(),
        'title': 'Agent Düzenle'
    })

from django.http import JsonResponse
from django.views.decorators.http import require_http_methods
from django.views.decorators.csrf import csrf_exempt  # Gerekirse ekleyin

@require_http_methods(["POST"])
def delete_agent(request, agent_id):
    try:
        agent = Agent.objects.get(id=agent_id)
        source = request.GET.get('source', 'agent_list')  # Varsayılan olarak agent_list'e yönlendir
        
        # Agent'ı silmeden önce gerekli bilgileri al
        group_id = agent.group.id if agent.group else None
        manager_id = agent.manager.id if agent.manager else None
        department_id = agent.manager.department.id if agent.manager and agent.manager.department else None
        
        # Agent'ı sil
        agent.delete()
        
        # AJAX isteği ise JSON yanıt döndür
        if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
            return JsonResponse({'status': 'success'})
            
        # Normal form submit ise, kaynağa göre yönlendir
        if source == 'group_detail' and group_id:
            messages.success(request, 'Personel başarıyla silindi.')
            return redirect('group_detail', group_id=group_id)
        elif source == 'manager_detail' and manager_id and department_id:
            messages.success(request, 'Personel başarıyla silindi.')
            return redirect('manager_detail', dept_pk=department_id, manager_pk=manager_id)
        else:
            messages.success(request, 'Personel başarıyla silindi.')
            return redirect('agent_list')
            
    except Agent.DoesNotExist:
        if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
            return JsonResponse({'status': 'error', 'message': 'Personel bulunamadı'}, status=404)
        messages.error(request, 'Personel bulunamadı.')
        return redirect('agent_list')
        
    except Exception as e:
        if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
            return JsonResponse({'status': 'error', 'message': str(e)}, status=400)
        messages.error(request, f'Bir hata oluştu: {str(e)}')
        return redirect('agent_list')

@login_required
@user_passes_test(is_superuser)
def group_list(request):
    groups = Group.objects.all()
    return render(request, 'groups/group_list.html', {'groups': groups})

@login_required
@user_passes_test(is_superuser)
def group_detail(request, group_id):
    group = get_object_or_404(Group, id=group_id)
    agents = group.agent_set.all().prefetch_related('agentschedule_set')
    agents = Agent.objects.filter(group=group)
    days = ['I', 'II', 'III', 'IV', 'V']
    
    if request.method == 'POST' and request.headers.get('X-Requested-With') == 'XMLHttpRequest':
        agent_id = request.POST.get('agent_id')
        date = request.POST.get('date')
        schedule_type = request.POST.get('schedule_type')
        
        agent = get_object_or_404(Agent, id=agent_id)
        schedule, created = AgentSchedule.objects.update_or_create(
            agent=agent,
            date=date,
            defaults={'schedule_type': schedule_type}
        )
        
        return JsonResponse({'status': 'success'})
    
    today = datetime.now()
    monday = today - timedelta(days=today.weekday())
    friday = monday + timedelta(days=4)
    
    week_dates = [(monday + timedelta(days=i)).date() for i in range(5)]
    
    return render(request, 'groups/group_detail.html', {
        'group': group, 'agents': agents, 'days': days,
        'week_start': monday.date(),
        'week_end': friday.date(),
        'week_dates': week_dates,
        'current_date': today.date(),
    })

@login_required
@user_passes_test(is_superuser)
def manager_list(request):
    managers = Manager.objects.all()
    return render(request, 'managers/manager_list.html', {'managers': managers})

@login_required
def manager_detail(request, dept_pk, manager_pk):
    department = get_object_or_404(Department, pk=dept_pk)
    manager = get_object_or_404(Manager, pk=manager_pk, department=department)
    agents = Agent.objects.filter(manager=manager)

    # Toplam değerleri hesapla
    total_icbari_1 = sum(agent.icbari_1 or 0 for agent in agents)
    total_icbari_2 = sum(agent.icbari_2 or 0 for agent in agents)
    total_konullu_1 = sum(agent.konullu_1 or 0 for agent in agents)
    total_konullu_2 = sum(agent.konullu_2 or 0 for agent in agents)

    context = {
        'department': department,
        'manager': manager,
        'agents': agents,
        'total_icbari_1': total_icbari_1,
        'total_icbari_2': total_icbari_2,
        'total_konullu_1': total_konullu_1,
        'total_konullu_2': total_konullu_2,
    }
    return render(request, 'managers/manager_detail.html', context)

@login_required
@user_passes_test(is_superuser)
def add_manager(request, dept_pk=None):
    department = get_object_or_404(Department, pk=dept_pk) if dept_pk else None
    
    if request.method == 'POST':
        form = ManagerForm(request.POST, request.FILES, department=department)
        if form.is_valid():
            manager = form.save()
            success_message = (
                "✅ Yönetici başarıyla eklendi!\n\n"
                "📋 Giriş Bilgileri:\n"
                f"👤 Kullanıcı adı: {manager.user.username}\n"
                f"🔑 Şifre: {form.cleaned_data['password']}\n\n"
                "⚠️ Lütfen bu bilgileri yöneticiye güvenli bir şekilde iletin."
            )
            messages.success(request, success_message)
            return redirect('department_detail', pk=dept_pk)
    else:
        form = ManagerForm(department=department)
    
    return render(request, 'managers/add_manager.html', {
        'form': form,
        'department': department
    })

@login_required
def edit_manager(request, dept_pk, manager_pk):
    department = get_object_or_404(Department, pk=dept_pk)
    manager = get_object_or_404(Manager, pk=manager_pk)
    
    # Sadece superuser veya ilgili manager erişebilir
    if not request.user.is_superuser:
        if not hasattr(request.user, 'manager') or request.user.manager != manager:
            raise PermissionDenied
    
    if request.method == 'POST':
        name = request.POST.get('name')
        surname = request.POST.get('surname')
        photo = request.FILES.get('photo')
        
        manager.name = name
        manager.surname = surname
        
        if photo:
            if manager.photo:
                manager.photo.delete(save=False)
            manager.photo = photo
        
        manager.save()
        messages.success(request, 'Yönetici başarıyla güncellendi.')
        return redirect('department_detail', pk=dept_pk)
            
    return render(request, 'managers/manager_form.html', {
        'manager': manager,
        'department': department
    })

@login_required
@user_passes_test(is_superuser)
def delete_manager(request, dept_pk, manager_pk):
    manager = get_object_or_404(Manager, pk=manager_pk)
    if request.method == 'POST':
        if manager.user:
            manager.user.delete()  # İlişkili user'ı da sil
        manager.delete()
        messages.success(request, 'Yönetici başarıyla silindi.')
        return redirect('department_detail', pk=dept_pk)
    return redirect('department_detail', pk=dept_pk)

@login_required
@user_passes_test(is_superuser)
def department_list(request):
    departments = Department.objects.all()
    return render(request, 'departments/department_list.html', {'departments': departments})

def add_department(request):
    if request.method == 'POST':
        form = DepartmentForm(request.POST)
        if form.is_valid():
            form.save()
            messages.success(request, 'Departman başarıyla oluşturuldu.')
            return redirect('department_list')
    else:
        form = DepartmentForm()
    return render(request, 'departments/department_form.html', {'form': form, 'title': 'Yeni Departman'})

def edit_department(request, pk):
    department = get_object_or_404(Department, pk=pk)
    if request.method == 'POST':
        form = DepartmentForm(request.POST, instance=department)
        if form.is_valid():
            form.save()
            messages.success(request, 'Departman başarıyla güncellendi.')
            return redirect('department_list')
    else:
        form = DepartmentForm(instance=department)
    return render(request, 'departments/department_form.html', {'form': form, 'title': 'Departman Düzenle'})

def delete_department(request, pk):
    department = get_object_or_404(Department, pk=pk)
    if request.method == 'POST':
        department.delete()
        messages.success(request, 'Departman başarıyla silindi.')
        return redirect('department_list')
    return redirect('department_list')

@login_required
@user_passes_test(is_superuser)
def department_detail(request, pk):
    department = get_object_or_404(Department, pk=pk)
    managers = department.manager_set.all()
    
    for manager in managers:
        manager.agent_count = Agent.objects.filter(manager=manager).count()

    if request.method == 'POST':
        form = ManagerForm(request.POST, department=department)
        if form.is_valid():
            form.save()
            messages.success(request, 'Yönetici başarıyla eklendi.')
            return redirect('department_detail', pk=department.pk)
    else:
        form = ManagerForm(department=department)
    
    return render(request, 'departments/department_detail.html', {
        'department': department,
        'managers': managers,
        'form': form
    })

from django.http import JsonResponse
from django.views.decorators.http import require_http_methods
import json

@require_http_methods(["POST"])
def update_agent_values(request):
    try:
        data = json.loads(request.body)
        agent_id = data.get('agent_id')
        field = data.get('field')
        value = data.get('value')

        agent = Agent.objects.get(id=agent_id)
        
        # Boş string kontrolü
        if value == '':
            value = None
            
        # Alan tipine göre değer dönüşümü
        if field in ['icbari_1', 'konullu_1']:
            value = int(value) if value is not None else None
        elif field in ['icbari_2', 'konullu_2']:
            value = float(value) if value is not None else None

        setattr(agent, field, value)
        agent.save()

        return JsonResponse({
            'status': 'success',
            'value': value
        })
    except Exception as e:
        return JsonResponse({
            'status': 'error',
            'message': str(e)
        }, status=400)

@login_required
def agent_delete(request, pk):
    agent = get_object_or_404(Agent, pk=pk)
    referer_url = request.META.get('HTTP_REFERER')
    
    if request.method == 'GET':  # GET isteği için de silme işlemini gerçekleştir
        # Eğer agent'ın fotoğrafı varsa, onu da sil
        if agent.photo:
            agent.photo.delete()
        
        agent.delete()
        messages.success(request, 'Agent başarıyla silindi.')
        
        # Önceki sayfaya yönlendir
        if referer_url:
            return redirect(referer_url)
        return redirect('agent_list')
    
    elif request.method == 'POST':
        # Eğer agent'ın fotoğrafı varsa, onu da sil
        if agent.photo:
            agent.photo.delete()
        
        agent.delete()
        messages.success(request, 'Agent başarıyla silindi.')
        
        # Önceki sayfaya yönlendir
        if referer_url:
            return redirect(referer_url)
        return redirect('agent_list')

def login_view(request):
    if request.method == 'POST':
        username = request.POST.get('username')
        password = request.POST.get('password')
        user = authenticate(request, username=username, password=password)
        
        if user is not None:
            login(request, user)
            
            # Eğer superuser ise ana sayfaya yönlendir
            if user.is_superuser:
                return redirect('agent_list')
            
            # Manager ise kendi sayfasına yönlendir
            try:
                if hasattr(user, 'manager'):
                    return redirect('manager_detail', 
                                 dept_pk=user.manager.department.id, 
                                 manager_pk=user.manager.id)
            except:
                pass
            
            # Diğer durumlar için ana sayfaya yönlendir
            return redirect('agent_list')
        else:
            messages.error(request, 'Kullanıcı adı veya şifre hatalı.')
    
    return render(request, 'registration/login.html')