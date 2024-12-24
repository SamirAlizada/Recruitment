from django.db import models

class Group(models.Model):
    name = models.CharField(max_length=50)  # Qrup adı (Səhər və ya Axşam)

    def __str__(self):
        return self.name

class Department(models.Model):
    name = models.CharField(max_length=100)

    def __str__(self):
        return self.name

class Manager(models.Model):
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
    created_at = models.DateTimeField(auto_now_add=True)
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
    group = models.ForeignKey(Group, on_delete=models.CASCADE, blank=False, null=False, default=get_default_group)
    manager = models.ForeignKey(Manager, on_delete=models.SET_NULL, blank=True, null=True)

    def __str__(self):
        return f"{self.name} {self.surname} - {self.status}"
