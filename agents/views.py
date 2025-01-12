# agents/views.py
from django.contrib.auth.decorators import login_required, user_passes_test
from django.shortcuts import render
from .models import Agent, Group, Manager, Department, AgentSchedule, DepartmentHead
from django.shortcuts import redirect, get_object_or_404, render
from .forms import AgentForm, DepartmentForm, ManagerForm, DepartmentHeadForm, GroupForm
from datetime import datetime, timedelta
from django.contrib import messages
from django.http import JsonResponse
from django import forms
import logging
from django.contrib.auth.models import User
from django.core.exceptions import PermissionDenied
from django.contrib.auth import authenticate, login
from django.urls import reverse
from django.contrib.admin.views.decorators import staff_member_required
from django.db.models import Count
from django.db.models.functions import TruncMonth
from django.utils import timezone
from datetime import datetime
import json
from django.db import models
from django.http import JsonResponse
from django.core.serializers.json import DjangoJSONEncoder
from django.db.models import Q

def is_superuser(user):
    return user.is_superuser

def is_department_head(user):
    try:
        return hasattr(user, 'departmenthead')
    except:
        return False

@login_required
def department_head_dashboard(request):
    if not is_department_head(request.user):
        raise PermissionDenied
    
    department_head = request.user.departmenthead
    department = department_head.department
    managers = Manager.objects.filter(department=department)
    agents = Agent.objects.filter(manager__in=managers)
    
    context = {
        'department': department,
        'managers': managers,
        'agents': agents,
    }
    return render(request, 'department_heads/department_head_dashboard.html', context)

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
    return render(request, 'agents/agent_list.html', {'agents': agents})

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
            try:
                # FİN değerini büyük harfe dönüştür
                fin = form.cleaned_data['fin'].upper()
                # FİN değerini form verilerine geri ekle
                form.instance.fin = fin
                
                form.save()
                
                # AJAX isteği ise JSON yanıt döndür
                if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
                    return JsonResponse({
                        'status': 'success',
                        'redirect_url': reverse('agent_list')
                    })
                
                messages.success(request, 'Agent uğurla əlavə edildi.')
                return redirect('agent_list')
            except Exception as e:
                if 'unique constraint' in str(e).lower() and 'fin' in str(e).lower():
                    error_message = 'Bu FIN nömrəsi artıq mövcuddur.'
                else:
                    error_message = 'Xəta baş verdi. Zəhmət olmasa yenidən cəhd edin.'
                
                # AJAX isteği ise JSON yanıt döndür
                if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
                    return JsonResponse({
                        'status': 'error',
                        'message': error_message
                    })
                
                messages.error(request, error_message)
        else:
            # AJAX isteği ise JSON yanıt döndür
            if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
                errors = []
                for field, field_errors in form.errors.items():
                    for error in field_errors:
                        errors.append(f"{form.fields[field].label}: {error}")
                return JsonResponse({
                    'status': 'error',
                    'message': '\n'.join(errors)
                })
            
            messages.error(request, 'Formanı doldurarkən xəta baş verdi. Yenidən cəhd edin.')
    else:
        form = AgentForm()

    groups = Group.objects.all()

    context = {
        'form': form,
        'status_choices': Agent._meta.get_field('status').choices,
        'groups': groups,
    }
    return render(request, 'agents/add_agent.html', context)

def update_agent_status(request, pk):
    agent = get_object_or_404(Agent, pk=pk)
    if request.method == 'POST':
        status = request.POST.get('status')
        if status in dict(Agent.STATUS_CHOICES):  # Geçerli bir durum mu kontrol et
            agent.status = status
            if status == "Təlimə gəlmədi":
                agent.group = None
            agent.save()
            return redirect('agent_list')

    return render(request, 'agents/update_status.html', {'agent': agent})

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
            logger.debug(f"Menecer əlavə edildi: {manager_data}")
        
        logger.debug(f"Dönülen manager listesi: {manager_list}")
        return JsonResponse(manager_list, safe=False)
        
    except Department.DoesNotExist:
        logger.error(f"Departman bulunamadı: {dept_id}")
        return JsonResponse({'error': 'Şöbə tapılmadı'}, status=404)
    except Exception as e:
        logger.error(f"Beklenmeyen hata: {str(e)}")
        return JsonResponse({'error': str(e)}, status=500)

def edit_agent(request, pk=None, agent_id=None):
    # pk veya agent_id parametrelerinden birini kullan
    agent_pk = pk if pk is not None else agent_id
    agent = get_object_or_404(Agent, pk=agent_pk)
    departments = Department.objects.all()
    managers = Manager.objects.all()
    referer_url = request.META.get('HTTP_REFERER')  # Önceki sayfanın URL'ini al
    
    if request.method == 'POST':
        form = AgentForm(request.POST, request.FILES, instance=agent)
        if form.is_valid():
            # FİN değerini büyük harfe dönüştür
            fin = form.cleaned_data['fin'].upper()
            # FİN değerini form verilerine geri ekle
            form.instance.fin = fin
            
            agent = form.save(commit=False)
            
            if agent.status == "Təlimə gəlmədi":
                agent.group = None
            elif agent.status in ['Təlimdən keçdi', 'İşə dəvət olundu', 'İşdən çıxdı']:
                department_id = request.POST.get('department')
                manager_id = request.POST.get('manager')
                
                if department_id and manager_id:
                    selected_manager = get_object_or_404(Manager, id=manager_id, department_id=department_id)
                    agent.manager = selected_manager
                    agent.department = selected_manager.department
                else:
                    form.add_error(None, 'Bu status üçün şöbə və menecerin seçilməsi məcburidir.')
                    return render(request, 'agents/edit_agent.html', {
                        'form': form,
                        'agent': agent,
                        'departments': departments,
                        'managers': managers,
                        'status_choices': Agent._meta.get_field('status').choices,
                        'groups': Group.objects.all(),
                        'title': 'Agentə Düzəliş Et'
                    })
            else:
                agent.manager = None
                if agent.status != "İşə gəlmədi":
                    agent.department = None
                else:
                    # İşə gəlmədi durumunda sadece departmanı güncelle
                    department_id = request.POST.get('department')
                    if department_id:
                        department = get_object_or_404(Department, id=department_id)
                        agent.department = department
                    agent.manager = None

            agent.save()
            messages.success(request, 'Agent uğurla yeniləndi.')
            
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
        'title': 'Agentə Düzəliş Et'
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
            messages.success(request, 'Agent uğurla silindi.')
            return redirect('group_detail', group_id=group_id)
        elif source == 'manager_detail' and manager_id and department_id:
            messages.success(request, 'Agent uğurla silindi.')
            return redirect('manager_detail', dept_pk=department_id, manager_pk=manager_id)
        else:
            messages.success(request, 'Agent uğurla silindi.')
            return redirect('agent_list')
            
    except Agent.DoesNotExist:
        if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
            return JsonResponse({'status': 'error', 'message': 'Agent tapılmadı'}, status=404)
        messages.error(request, 'Agent tapılmadı.')
        return redirect('agent_list')
        
    except Exception as e:
        if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
            return JsonResponse({'status': 'error', 'message': str(e)}, status=400)
        messages.error(request, f'Xəta baş verdi: {str(e)}')
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
    
    # Check and update failed agents' group field
    today = datetime.now().date()
    failed_agents = Agent.objects.filter(
        group=group,
        status='Təlimi keçə bilmədi'
    )
    
    for agent in failed_agents:
        if agent.training_period and 'end' in agent.training_period:
            training_end = datetime.strptime(agent.training_period['end'], '%Y-%m-%d').date()
            if today > training_end:
                agent.group = None
                agent.save()
    
    agents = group.agent_set.all().prefetch_related('agentschedule_set')
    agents = Agent.objects.filter(group=group)
    available_agents = Agent.objects.filter(status='Müsahibədən keçdi', group__isnull=True)
    days = ['I', 'II', 'III', 'IV', 'V']
    departments = Department.objects.all()
    
    if request.method == 'POST' and request.headers.get('X-Requested-With') == 'XMLHttpRequest':
        if 'bulk_add' in request.POST:
            try:
                agent_ids = json.loads(request.POST.get('agent_ids', '[]'))
                today = datetime.now()
                monday = today - timedelta(days=today.weekday())
                friday = monday + timedelta(days=4)
                
                for agent_id in agent_ids:
                    agent = get_object_or_404(Agent, id=agent_id)
                    agent.group = group
                    agent.status = 'Təlimə dəvət olundu'
                    agent.training_period = {
                        'start': monday.strftime('%Y-%m-%d'),
                        'end': friday.strftime('%Y-%m-%d')
                    }
                    agent.save()
                
                return JsonResponse({'status': 'success'})
            except json.JSONDecodeError:
                return JsonResponse({'status': 'error', 'message': 'Invalid agent IDs format'})
            except Agent.DoesNotExist:
                return JsonResponse({'status': 'error', 'message': 'One or more agents not found'})
            except Exception as e:
                return JsonResponse({'status': 'error', 'message': str(e)})
        elif 'add_agent' in request.POST:
            agent_id = request.POST.get('agent_id')
            agent = get_object_or_404(Agent, id=agent_id)
            agent.group = group
            agent.status = 'Təlimə dəvət olundu'
            
            # Set training period when agent is added to group
            today = datetime.now()
            monday = today - timedelta(days=today.weekday())
            friday = monday + timedelta(days=4)
            agent.training_period = {
                'start': monday.strftime('%Y-%m-%d'),
                'end': friday.strftime('%Y-%m-%d')
            }
            
            agent.save()
            return JsonResponse({'status': 'success'})
        else:
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
        'group': group, 
        'agents': agents, 
        'available_agents': available_agents,
        'days': days,
        'week_start': monday.date(),
        'week_end': friday.date(),
        'week_dates': week_dates,
        'current_date': today.date(),
        'departments': departments,
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
def add_manager(request, dept_pk=None):
    department = get_object_or_404(Department, pk=dept_pk) if dept_pk else None
    
    # Check if user is superuser or department head of this department
    if not request.user.is_superuser and (not hasattr(request.user, 'departmenthead') or request.user.departmenthead.department != department):
        raise PermissionDenied
    
    if request.method == 'POST':
        form = ManagerForm(request.POST, request.FILES, department=department)
        if form.is_valid():
            manager = form.save()
            success_message = (
                "✅ Menecer uğurla əlavə edildi!\n\n"
                "📋 Giriş Məlumatı:\n"
                f"👤 İstifadəçi adı: {manager.user.username}\n"
                f"🔑 Şifrə: {form.cleaned_data['password']}\n\n"
                "⚠️ Zəhmət olmasa bu məlumatı təhlükəsiz şəkildə menecerə yönləndirin."
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
    
    # Check if user is superuser or department head of this department
    if not request.user.is_superuser and (not hasattr(request.user, 'departmenthead') or request.user.departmenthead.department != department):
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
        messages.success(request, 'Menecer uğurıa yeniləndi.')
        return redirect('department_detail', pk=dept_pk)
            
    return render(request, 'managers/manager_form.html', {
        'manager': manager,
        'department': department
    })

@login_required
def delete_manager(request, dept_pk, manager_pk):
    department = get_object_or_404(Department, pk=dept_pk)
    manager = get_object_or_404(Manager, pk=manager_pk)
    
    # Check if user is superuser or department head of this department
    if not request.user.is_superuser and (not hasattr(request.user, 'departmenthead') or request.user.departmenthead.department != department):
        raise PermissionDenied
    
    if request.method == 'POST':
        if manager.user:
            manager.user.delete()  # İlişkili user'ı da sil
        manager.delete()
        messages.success(request, 'Menecer uğurla silindi.')
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
            messages.success(request, 'Şöbə uğurla yaradıldı.')
            return redirect('department_list')
    else:
        form = DepartmentForm()
    return render(request, 'departments/department_form.html', {'form': form, 'title': 'Yeni Şöbə'})

def edit_department(request, pk):
    department = get_object_or_404(Department, pk=pk)
    if request.method == 'POST':
        form = DepartmentForm(request.POST, instance=department)
        if form.is_valid():
            form.save()
            messages.success(request, 'Şöbə uğurla yeniləndi.')
            return redirect('department_list')
    else:
        form = DepartmentForm(instance=department)
    return render(request, 'departments/department_form.html', {'form': form, 'title': 'Şöbəyə Düzəliş Et'})

def delete_department(request, pk):
    department = get_object_or_404(Department, pk=pk)
    if request.method == 'POST':
        department.delete()
        messages.success(request, 'Şöbə uğurla silindi.')
        return redirect('department_list')
    return redirect('department_list')

@login_required
def department_detail(request, pk):
    # Eğer şöbə müdürü ise, sadece kendi departmanını görebilir
    if hasattr(request.user, 'departmenthead'):
        if request.user.departmenthead.department.id != pk:
            raise PermissionDenied
        department = request.user.departmenthead.department
    else:
        # Admin tüm departmanları görebilir
        department = get_object_or_404(Department, pk=pk)
    
    # Get new agents (agents with no manager assigned)
    new_agents = Agent.objects.filter(
        department=department,
        manager__isnull=True,
        status='İşə dəvət olundu'
    )
    
    # Departman başkanını al
    try:
        department_head = DepartmentHead.objects.get(department=department)
    except DepartmentHead.DoesNotExist:
        department_head = None
    
    managers = department.manager_set.all()
    for manager in managers:
        manager.agent_count = Agent.objects.filter(manager=manager).count()

    context = {
        'department': department,
        'department_head': department_head,
        'managers': managers,
        'new_agents': new_agents,
    }
    
    return render(request, 'departments/department_detail.html', context)

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
        messages.success(request, 'Agent uğurla silindi.')
        
        # Önceki sayfaya yönlendir
        if referer_url:
            return redirect(referer_url)
        return redirect('agent_list')
    
    elif request.method == 'POST':
        # Eğer agent'ın fotoğrafı varsa, onu da sil
        if agent.photo:
            agent.photo.delete()
        
        agent.delete()
        messages.success(request, 'Agent uğurla silindi.')
        
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
            
            # Her kullanıcı tipini ayrı ayrı kontrol et
            if user.is_superuser:
                return redirect('agent_list')
            elif hasattr(user, 'manager'):  # Manager tipi kullanıcı
                return redirect('manager_detail', dept_pk=user.manager.department.id, manager_pk=user.manager.id)
            elif hasattr(user, 'departmenthead'):  # Şöbə müdürü tipi kullanıcı
                return redirect('department_detail', pk=user.departmenthead.department.id)
            else:
                messages.error(request, 'İstifadəçi tipi tanınmadı.')
                return redirect('login')
        else:
            messages.error(request, 'İstifadəçi adı və ya şifrə yanlışdır.')
    
    return render(request, 'registration/login.html')

@login_required
@user_passes_test(is_superuser)
def add_department_head(request, dept_pk):
    department = get_object_or_404(Department, pk=dept_pk)
    
    if request.method == 'POST':
        form = DepartmentHeadForm(request.POST, request.FILES, initial={'department': department})
        if form.is_valid():
            department_head = form.save()
            success_message = (
                "✅ Şöbə müdürü uğurla əlavə edildi!\n\n"
                "📋 Giriş Məlumatı:\n"
                f"👤 İstifadəçi adı: {form.cleaned_data['username']}\n"
                f"🔑 Şifrə: {form.cleaned_data['password']}\n\n"
                "⚠️ Zəhmət olmasa bu məlumatı təhlükəsiz şəkildə şöbə müdürünə yönləndirin."
            )
            messages.success(request, success_message)
            return redirect('department_detail', pk=department_head.department.id)
        else:
            messages.error(request, 'Xəta baş verdi. Zəhmət olmasa məlumatları yoxlayın.')
    else:
        form = DepartmentHeadForm(initial={'department': department})
    
    return render(request, 'department_heads/add_department_head.html', {
        'form': form,
        'title': 'Yeni Şöbə Müdürü',
        'department': department
    })

@login_required
@user_passes_test(is_superuser)
def edit_department_head(request, dept_pk, head_pk):
    department = get_object_or_404(Department, pk=dept_pk)
    department_head = get_object_or_404(DepartmentHead, pk=head_pk, department=department)
    
    if request.method == 'POST':
        form = DepartmentHeadForm(request.POST, request.FILES, instance=department_head, initial={'department': department})
        if form.is_valid():
            department_head = form.save(commit=False)
            
            # Handle photo update
            if 'photo' in request.FILES:
                # Delete old photo if exists
                if department_head.photo:
                    try:
                        old_photo_path = department_head.photo.path
                        import os
                        if os.path.exists(old_photo_path):
                            os.remove(old_photo_path)
                    except Exception:
                        pass  # If file deletion fails, continue anyway
                
                # Set new photo
                department_head.photo = request.FILES['photo']
            
            department_head.save()
            messages.success(request, 'Şöbə müdürü uğurla yeniləndi.')
            return redirect('department_detail', pk=department.id)
    else:
        form = DepartmentHeadForm(instance=department_head, initial={'department': department})
    
    return render(request, 'department_heads/edit_department_head.html', {
        'form': form,
        'title': 'Şöbə Müdürünə Düzəliş Et',
        'department': department,
        'department_head': department_head
    })

@login_required
@user_passes_test(is_superuser)
def delete_department_head(request, dept_pk, head_pk):
    department = get_object_or_404(Department, pk=dept_pk)
    department_head = get_object_or_404(DepartmentHead, pk=head_pk, department=department)
    
    if request.method == 'POST':
        # Önce user'ı sil
        if department_head.user:
            department_head.user.delete()
        # Sonra department head'i sil
        department_head.delete()
        messages.success(request, 'Şöbə müdürü uğurla silindi.')
    
    return redirect('department_detail', pk=dept_pk)

@login_required
@require_http_methods(["POST"])
def transfer_to_department(request):
    print("Transfer request received")  # Debug için
    print("Headers:", request.headers)  # Debug için
    print("POST data:", request.POST)  # Debug için
    
    if not request.headers.get('X-Requested-With') == 'XMLHttpRequest':
        return JsonResponse({'status': 'error', 'message': 'Invalid request'}, status=400)
    
    try:
        department_id = request.POST.get('department_id')
        group_id = request.POST.get('group_id')
        
        print(f"Department ID: {department_id}, Group ID: {group_id}")  # Debug için
        
        if not department_id or not group_id:
            return JsonResponse({
                'status': 'error',
                'message': 'department_id and group_id are required'
            }, status=400)
        
        department = Department.objects.get(id=department_id)
        group = Group.objects.get(id=group_id)
        
        # Get all agents in the group except those with 'Təlimi keçə bilmədi' status
        agents = Agent.objects.filter(group=group).exclude(status='Təlimi keçə bilmədi')
        
        if not agents.exists():
            return JsonResponse({
                'status': 'error',
                'message': 'No eligible agents found in this group'
            }, status=400)
            
        print(f"Found {agents.count()} agents to transfer")  # Debug için
        
        from datetime import date
        current_date = date.today()
            
        # Transfer edilecek agent sayısı
        transfer_count = agents.count()
            
        agents.update(
            department=department,
            status='İşə dəvət olundu',
            group=None,  # Remove from group
            department_transfer_date=current_date  # Set transfer date to today
        )
        
        # Get count of failed agents that were not transferred
        failed_agents_count = Agent.objects.filter(group=group, status='Təlimi keçə bilmədi').count()
        
        success_message = f'{transfer_count} agent uğurla transfer edildi.'
        if failed_agents_count > 0:
            success_message += f'\n{failed_agents_count} agent "Təlimi keçə bilmədi" statusunda olduğu üçün transfer edilmədi.'
        
        return JsonResponse({
            'status': 'success',
            'message': success_message,
            'redirect_url': reverse('department_detail', kwargs={'pk': department_id})
        })
    except Department.DoesNotExist:
        return JsonResponse({
            'status': 'error',
            'message': 'Department not found'
        }, status=404)
    except Group.DoesNotExist:
        return JsonResponse({
            'status': 'error',
            'message': 'Group not found'
        }, status=404)
    except Exception as e:
        print(f"Error occurred: {str(e)}")  # Debug için
        return JsonResponse({
            'status': 'error',
            'message': str(e)
        }, status=400)

@login_required
@require_http_methods(["POST"])
def assign_manager(request):
    # Check if user is superuser or department head
    if not (request.user.is_superuser or hasattr(request.user, 'departmenthead')):
        return JsonResponse({'status': 'error', 'message': 'Permission denied'}, status=403)
    
    if not request.headers.get('X-Requested-With') == 'XMLHttpRequest':
        return JsonResponse({'status': 'error', 'message': 'Invalid request'}, status=400)
    
    agent_id = request.POST.get('agent_id')
    manager_id = request.POST.get('manager_id')
    
    try:
        agent = Agent.objects.get(id=agent_id)
        manager = Manager.objects.get(id=manager_id)
        
        # If user is department head, check if they have permission for this department
        if hasattr(request.user, 'departmenthead'):
            if request.user.departmenthead.department != agent.department:
                return JsonResponse({
                    'status': 'error',
                    'message': 'You do not have permission for this department'
                }, status=403)
        
        # Check if manager belongs to agent's department
        if agent.department != manager.department:
            return JsonResponse({
                'status': 'error',
                'message': 'Manager does not belong to the same department'
            }, status=400)
        
        agent.manager = manager
        agent.save()
        
        return JsonResponse({'status': 'success'})
    except Agent.DoesNotExist:
        return JsonResponse({'status': 'error', 'message': 'Agent not found'}, status=404)
    except Manager.DoesNotExist:
        return JsonResponse({'status': 'error', 'message': 'Manager not found'}, status=404)
    except Exception as e:
        return JsonResponse({'status': 'error', 'message': str(e)}, status=400)

@staff_member_required
def hesabat_view(request):
    # Get date range from request
    start_date = request.GET.get('start_date')
    end_date = request.GET.get('end_date')
    
    # Format dates for display
    formatted_start_date = None
    formatted_end_date = None
    start_date_obj = None
    end_date_obj = None
    
    # Base queryset
    agents = Agent.objects.all()
    
    # Apply date filter if provided
    if start_date and end_date:
        try:
            start_date_obj = datetime.strptime(start_date, '%Y-%m-%d')
            end_date_obj = datetime.strptime(end_date, '%Y-%m-%d')
            
            # Format dates for display
            formatted_start_date = start_date_obj.strftime('%d.%m.%Y')
            formatted_end_date = end_date_obj.strftime('%d.%m.%Y')
            
            # Filter agents
            agents = agents.filter(created_at__date__range=[start_date_obj.date(), end_date_obj.date()])
        except ValueError:
            pass
    else:
        # If no date range provided, use last 12 months
        end_date_obj = timezone.now()
        start_date_obj = end_date_obj - timedelta(days=365)

    # Overall statistics
    total_agents = agents.filter(status__in=['İşə dəvət olundu', 'İşdən çıxdı']).count()
    active_agents = agents.filter(status__in=['İşə dəvət olundu']).count()
    inactive_agents = agents.filter(status='İşdən çıxdı').count()

    # Recruitment Statistics
    added_agents_count = agents.count()  # Total agents added in the date range
    
    # For invited_to_training_count, we'll count all agents except those who Təlimə gəlmədi
    invited_to_training_count = agents.exclude(status="Təlimə gəlmədi").filter(
        Q(status='Təlimə dəvət olundu') |  # Current invites
        Q(status__in=[  # Past invites who moved to any other status (except Təlimə gəlmədi)
            'Təlimdən keçdi',
            'İşə dəvət olundu',
            "İşə gəlmədi",
            'İşdən çıxdı',
            'Təlimi keçə bilmədi'
        ])
    ).count()
    
    didnt_come_to_training_count = agents.filter(status="Təlimə gəlmədi").count()

    # Trainer Statistics
    passed_training_count = agents.filter(
        Q(status='Təlimdən keçdi') |  # Current passed training
        Q(status__in=['İşə dəvət olundu', "İşə gəlmədi", 'İşdən çıxdı'])  # Past passed training who moved forward
    ).count()
    
    failed_training_count = agents.filter(status='Təlimi keçə bilmədi').count()

    # Department statistics
    department_stats = Department.objects.annotate(
        total_agents=Count(
            'agent',
            filter=models.Q(
                agent__status__in=['İşə dəvət olundu', 'İşdən çıxdı', "İşə gəlmədi"],
                agent__created_at__date__range=[start_date_obj.date(), end_date_obj.date()]
            )
        ),
        active_agents=Count(
            'agent',
            filter=models.Q(
                agent__status__in=['İşə dəvət olundu'],
                agent__created_at__date__range=[start_date_obj.date(), end_date_obj.date()]
            )
        ),
        inactive_agents=Count(
            'agent',
            filter=models.Q(
                agent__status='İşdən çıxdı',
                agent__created_at__date__range=[start_date_obj.date(), end_date_obj.date()]
            )
        ),
        didnt_come_to_work=Count(
            'agent',
            filter=models.Q(
                agent__status="İşə gəlmədi",
                agent__created_at__date__range=[start_date_obj.date(), end_date_obj.date()]
            )
        )
    )

    context = {
        'total_agents': total_agents,
        'active_agents': active_agents,
        'inactive_agents': inactive_agents,
        'added_agents_count': added_agents_count,
        'invited_to_training_count': invited_to_training_count,
        'didnt_come_to_training_count': didnt_come_to_training_count,
        'passed_training_count': passed_training_count,
        'failed_training_count': failed_training_count,
        'department_stats': department_stats,
        'formatted_start_date': formatted_start_date,
        'formatted_end_date': formatted_end_date
    }

    return render(request, 'reports/hesabat.html', context)

# @login_required
# @user_passes_test(is_superuser)
# def get_agents_by_type(request, agent_type):
#     print("Getting agentsssssssssssssssss")
#     try:
#         # Get date range from request
#         start_date = request.GET.get('start_date')
#         end_date = request.GET.get('end_date')
        
#         print(f"Fetching agents of type: {agent_type}")  # Debug log
#         print(f"Date range: {start_date} - {end_date}")  # Debug log
        
#         # Base queryset
#         agents = Agent.objects.select_related('department', 'manager').all()
        
#         # Apply date filter if provided
#         if start_date and end_date:
#             try:
#                 start_date_obj = datetime.strptime(start_date, '%Y-%m-%d')
#                 end_date_obj = datetime.strptime(end_date, '%Y-%m-%d')
#                 agents = agents.filter(created_at__date__range=[start_date_obj.date(), end_date_obj.date()])
#             except ValueError as e:
#                 print(f"Date parsing error: {e}")  # Debug log
#                 return JsonResponse({'error': 'Invalid date format'}, status=400)
        
#         # Filter by agent type
#         if agent_type == 'total':
#             agents = agents.filter(status__in=['İşə dəvət olundu', 'İşdən çıxdı'])
#         elif agent_type == 'active':
#             agents = agents.filter(status__in=['İşə dəvət olundu'])
#         elif agent_type == 'inactive':
#             agents = agents.filter(status='İşdən çıxdı')
#         else:
#             return JsonResponse({'error': 'Invalid agent type'}, status=400)
        
#         print(f"Found {agents.count()} agents")  # Debug log
        
#         # Prepare data for response
#         agent_data = []
#         for agent in agents:
#             agent_data.append({
#                 'photo': agent.photo.url if agent.photo else None,
#                 'name': agent.name,
#                 'surname': agent.surname,
#                 'department': agent.department.name if agent.department else None,
#                 'manager': f"{agent.manager.name} {agent.manager.surname}" if agent.manager else None
#             })
        
#         print(f"Returning {len(agent_data)} agents")  # Debug log
#         return JsonResponse(agent_data, safe=False)
        
#     except Exception as e:
#         print(f"Error in get_agents_by_type: {str(e)}")  # Debug log
#         return JsonResponse({'error': str(e)}, status=500)

@login_required
@require_http_methods(["POST"])
def mark_agent_didnt_come(request):
    if not request.user.is_superuser and not hasattr(request.user, 'departmenthead'):
        return JsonResponse({'error': 'Permission denied'}, status=403)
    
    agent_id = request.POST.get('agent_id')
    if not agent_id:
        return JsonResponse({'error': 'Agent ID is required'}, status=400)
    
    try:
        agent = Agent.objects.get(id=agent_id)
        # Only update the status, keeping the department and other data intact
        agent.status = "İşə gəlmədi"
        agent.save(update_fields=['status'])  # Only update the status field
        return JsonResponse({'success': True})
    except Agent.DoesNotExist:
        return JsonResponse({'error': 'Agent not found'}, status=404)
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)

@login_required
@user_passes_test(is_superuser)
def add_group(request):
    if request.method == 'POST':
        form = GroupForm(request.POST)
        if form.is_valid():
            try:
                group = form.save()
                messages.success(request, 'Qrup uğurla əlavə edildi.')
                return redirect('group_list')
            except Exception as e:
                print(f"Error saving group: {str(e)}")  # Debug print
                messages.error(request, f'Xəta baş verdi: {str(e)}')
        else:
            print(f"Form errors: {form.errors}")  # Debug print
            messages.error(request, f'Xəta baş verdi: {form.errors}')
    return redirect('group_list')

@login_required
@user_passes_test(is_superuser)
def edit_group(request, pk):
    group = get_object_or_404(Group, pk=pk)
    if request.method == 'POST':
        form = GroupForm(request.POST, instance=group)
        if form.is_valid():
            form.save()
            messages.success(request, 'Qrup uğurla yeniləndi.')
        else:
            messages.error(request, 'Xəta baş verdi. Zəhmət olmasa yenidən cəhd edin.')
    return redirect('group_list')

@login_required
@user_passes_test(is_superuser)
def delete_group(request, pk):
    group = get_object_or_404(Group, pk=pk)
    if request.method == 'POST':
        group.delete()
        messages.success(request, 'Qrup uğurla silindi.')
    return redirect('group_list')