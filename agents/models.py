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

def get_default_group():
    # İlk mövcud qrupun ID-sini qaytarır
    return Group.objects.first().id if Group.objects.exists() else None

class Agent(models.Model):
    photo = models.ImageField(upload_to='agent_photos/', blank=True, null=True)
    name = models.CharField(max_length=100)
    surname = models.CharField(max_length=100)
    fin = models.CharField(max_length=7)
    phone = models.CharField(max_length=15, null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    icbari_1 = models.IntegerField(null=True, blank=True)
    icbari_2 = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    konullu_1 = models.IntegerField(null=True, blank=True)
    konullu_2 = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    status = models.CharField(
        max_length=20,
        choices=[
            ('Passed to Interview', 'Passed to Interview'),
            ('Invited to Training', 'Invited to Training'),
            ('Failed to Training', 'Failed to Training'),
            ('Passed to Training', 'Passed to Training'),
            ('Invited to Work', 'Invited to Work'),
            ('Failed to Work', 'Failed to Work'),
            ('Passed to Work', 'Passed to Work'),
        ],
        default="Passed to Interview"
    )
    group = models.ForeignKey(Group, on_delete=models.CASCADE, blank=True, null=True)
    manager = models.ForeignKey(Manager, on_delete=models.SET_NULL, blank=True, null=True)

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
