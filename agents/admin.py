from django.contrib import admin
from .models import Agent, Group, Manager, Department

admin.site.register(Agent)
admin.site.register(Group)
admin.site.register(Manager)
admin.site.register(Department)
