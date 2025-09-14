from django.contrib.auth.models import AbstractUser
from django.db import models
from django.core.validators import RegexValidator


class User(AbstractUser):
    USER_ROLES = [
        ('admin', 'Admin'),
        ('coordinator', 'Coordinator'),
        ('general', 'General'),
    ]
    
    role = models.CharField(max_length=20, choices=USER_ROLES, default='general')
    mobile_number = models.CharField(
        max_length=15,
        validators=[RegexValidator(regex=r'^\+?1?\d{9,15}$', message="Phone number must be entered in the format: '+999999999'. Up to 15 digits allowed.")],
        blank=True
    )
    is_first_login = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        db_table = 'users'
        
    def __str__(self):
        return f"{self.get_full_name()} ({self.email})"
        
    @property
    def full_name(self):
        return f"{self.first_name} {self.last_name}".strip()


class AuditTrail(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='audit_trails')
    impersonated_user = models.ForeignKey(User, on_delete=models.CASCADE, null=True, blank=True, related_name='impersonated_trails')
    action = models.CharField(max_length=255)
    model_name = models.CharField(max_length=100)
    object_id = models.CharField(max_length=100)
    changes = models.JSONField(default=dict)
    timestamp = models.DateTimeField(auto_now_add=True)
    ip_address = models.GenericIPAddressField(null=True, blank=True)
    
    class Meta:
        db_table = 'audit_trails'
        ordering = ['-timestamp']
        
    def __str__(self):
        return f"{self.user.username} - {self.action} - {self.timestamp}"