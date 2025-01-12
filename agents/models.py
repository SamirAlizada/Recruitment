from django.db import models
from django.contrib.auth.models import User

class Group(models.Model):
    name = models.CharField(max_length=100)  # Qrup adı (Səhər və ya Axşam)
    members = models.ManyToManyField('Agent', related_name='groups', blank=True)

    def __str__(self):
        return self.name

    @property
    def member_count(self):
        return self.members.count()

class Department(models.Model):
    name = models.CharField(max_length=100)

    def __str__(self):
        return self.name

class Manager(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE, null=True)
    photo = models.ImageField(upload_to='manager_photos/', blank=True, null=True)
    name = models.CharField(max_length=50)
    surname = models.CharField(max_length=50)
    department = models.ForeignKey(Department, on_delete=models.CASCADE)

    def __str__(self):
        return self.name

class DepartmentHead(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    photo = models.ImageField(upload_to='department_head_photos/', blank=True, null=True)
    name = models.CharField(max_length=50)
    surname = models.CharField(max_length=50)
    department = models.OneToOneField(Department, on_delete=models.CASCADE)

    def __str__(self):
        return f"{self.name} {self.surname} - {self.department.name}"

def get_default_group():
    # İlk mövcud qrupun ID-sini qaytarır
    return Group.objects.first().id if Group.objects.exists() else None

class Agent(models.Model):
    STATUS_CHOICES = [
        ('Müsahibədən keçdi', 'Müsahibədən keçdi'),
        ('Təlimə dəvət oldu', 'Təlimə dəvət oldu'),
        ("Təlimə gəlmədi", "Təlimə gəlmədi"),
        ('Təlimi keçə bilmədi', 'Təlimi keçə bilmədi'),
        ('Təlimdən keçdi', 'Təlimdən keçdi'),
        ("İşə gəlmədi", "İşə gəlmədi"),
        ('İşə dəvət olundu', 'İşə dəvət olundu'),
        ('İşdən çıxdı', 'İşdən çıxdı'),
    ]
    
    name = models.CharField(max_length=100)
    surname = models.CharField(max_length=100)
    fin = models.CharField(max_length=7, unique=True)
    phone = models.CharField(max_length=20)
    photo = models.ImageField(upload_to='agent_photos/', null=True, blank=True)
    status = models.CharField(max_length=50, choices=STATUS_CHOICES, default='Müsahibədən keçdi')
    created_at = models.DateTimeField(auto_now_add=True)
    group = models.ForeignKey('Group', on_delete=models.SET_NULL, null=True, blank=True)
    manager = models.ForeignKey('Manager', on_delete=models.SET_NULL, null=True, blank=True)
    department = models.ForeignKey('Department', on_delete=models.SET_NULL, null=True, blank=True)
    icbari_1 = models.IntegerField(null=True, blank=True)
    icbari_2 = models.FloatField(null=True, blank=True)
    konullu_1 = models.IntegerField(null=True, blank=True)
    konullu_2 = models.FloatField(null=True, blank=True)
    training_period = models.JSONField(null=True, blank=True, help_text='Training period start and end dates in format {"start": "YYYY-MM-DD", "end": "YYYY-MM-DD"}')
    department_transfer_date = models.DateField(null=True, blank=True, help_text='Date when agent was transferred to department')

    def __str__(self):
        return f"{self.name} {self.surname} - {self.status}"

class AgentSchedule(models.Model):
    agent = models.ForeignKey(Agent, on_delete=models.CASCADE)
    date = models.DateField()
    schedule_type = models.CharField(max_length=2, choices=[
        ('i', 'i/e'),
        ('qb', 'qb'),
    ])

    class Meta:
        unique_together = ['agent', 'date']  # Bir agent'ın bir günde sadece bir schedule'ı olabilir
