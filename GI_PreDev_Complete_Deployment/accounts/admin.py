from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from .models import User, AuditTrail


@admin.register(User)
class UserAdmin(BaseUserAdmin):
    list_display = ('username', 'email', 'first_name', 'last_name', 'role', 'is_active', 'date_joined')
    list_filter = ('role', 'is_active', 'is_staff', 'date_joined')
    search_fields = ('username', 'email', 'first_name', 'last_name')
    ordering = ('username',)
    
    fieldsets = BaseUserAdmin.fieldsets + (
        ('PRE System', {
            'fields': ('role', 'mobile_number', 'is_first_login')
        }),
    )
    
    add_fieldsets = BaseUserAdmin.add_fieldsets + (
        ('PRE System', {
            'fields': ('role', 'mobile_number')
        }),
    )


@admin.register(AuditTrail)
class AuditTrailAdmin(admin.ModelAdmin):
    list_display = ('user', 'impersonated_user', 'action', 'model_name', 'timestamp')
    list_filter = ('model_name', 'timestamp', 'user__role')
    search_fields = ('user__username', 'impersonated_user__username', 'action', 'model_name')
    readonly_fields = ('user', 'impersonated_user', 'action', 'model_name', 'object_id', 'changes', 'timestamp', 'ip_address')
    ordering = ('-timestamp',)
    
    def has_add_permission(self, request):
        return False
    
    def has_change_permission(self, request, obj=None):
        return False