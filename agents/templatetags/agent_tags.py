from django import template

register = template.Library()

@register.filter
def get_schedule(schedules, date):
    """Belirli bir tarihteki schedule'ı döndürür"""
    schedule = schedules.filter(date=date).first()
    return schedule.schedule_type if schedule else '' 