from django.contrib import admin
from django.utils.html import format_html
from .models import AuditLog

@admin.register(AuditLog)
class AuditLogAdmin(admin.ModelAdmin):
    """
    Admin configuration for AuditLog
    Note: Audit logs are read-only and cannot be edited or deleted
    """
    
    list_display = [
        'id', 
        'tenant', 
        'action_colored', 
        'record_type', 
        'record_id', 
        'created_at'
    ]
    list_filter = ['action', 'record_type', 'created_at', 'tenant']
    search_fields = ['record_id', 'data', 'actor_id']
    readonly_fields = [
        'id', 
        'tenant', 
        'actor_id', 
        'action', 
        'record_type', 
        'record_id',
        'before_hash', 
        'after_hash', 
        'data', 
        'previous_version',
        'ip_address',
        'user_agent',
        'created_at'
    ]
    date_hierarchy = 'created_at'
    ordering = ['-created_at']
    
    fieldsets = (
        ('Basic Information', {
            'fields': ('id', 'tenant', 'actor_id', 'action', 'created_at')
        }),
        ('Record Information', {
            'fields': ('record_type', 'record_id', 'previous_version')
        }),
        ('Hash Information', {
            'fields': ('before_hash', 'after_hash')
        }),
        ('Additional Data', {
            'fields': ('data', 'ip_address', 'user_agent')
        }),
    )
    
    def has_add_permission(self, request):
        """Prevent adding audit logs through admin"""
        return False
    
    def has_change_permission(self, request, obj=None):
        """Prevent changing audit logs"""
        return False
    
    def has_delete_permission(self, request, obj=None):
        """Prevent deleting audit logs"""
        return False
    
    def action_colored(self, obj):
        """Display action with color coding"""
        colors = {
            'CREATE': 'green',
            'UPDATE': 'blue',
            'DELETE': 'red',
            'READ': 'gray',
            'VERIFY': 'orange',
            'LOGIN': 'purple',
            'LOGOUT': 'purple',
            'EXPORT': 'brown',
            'IMPORT': 'brown',
        }
        color = colors.get(obj.action, 'black')
        return format_html(
            '<span style="color: {}; font-weight: bold;">{}</span>',
            color,
            obj.get_action_display()
        )
    action_colored.short_description = 'Action'