from django import template
from datetime import datetime
from ..models import AgentSchedule

register = template.Library()

@register.filter(name='az_month')
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
    
    # String içindeki ay adını bul ve değiştir
    for eng, az in az_months.items():
        if eng in str(value):
            return str(value).replace(eng, az)
    return value 

@register.filter(name='get_schedule')
def get_schedule(agent, date):
    try:
        schedule = AgentSchedule.objects.get(agent=agent, date=date)
        return schedule.schedule_type
    except AgentSchedule.DoesNotExist:
        return None 

@register.filter
def split(value, delimiter='\n'):
    """
    Returns the string split by delimiter.
    """
    return value.split(delimiter) 