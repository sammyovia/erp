from django.contrib import admin
from django.urls import reverse
from django.utils.html import format_html
from .models import Tenant, TenantUser

@admin.register(Tenant)
class TenantAdmin(admin.ModelAdmin):
    """Admin configuration for Tenant model"""
    
    list_display = [
        'name', 
        'slug', 
        'is_active', 
        'user_count_display', 
        'created_at'
    ]
    list_filter = ['is_active', 'created_at']
    search_fields = ['name', 'slug']
    readonly_fields = ['id', 'created_at', 'updated_at']
    prepopulated_fields = {'slug': ('name',)}
    ordering = ['name']
    
    fieldsets = (
        ('Basic Information', {
            'fields': ('id', 'name', 'slug', 'is_active')
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )
    
    def user_count_display(self, obj):
        """Display user count with link"""
        count = obj.user_count
        if count > 0:
            url = reverse('admin:tenants_tenantuser_changelist') + f'?tenant__id__exact={obj.id}'
            return format_html('<a href="{}">{}</a>', url, count)
        return "0"
    user_count_display.short_description = 'Users'
    
    def get_queryset(self, request):
        """Optimize query with annotation"""
        qs = super().get_queryset(request)
        return qs.prefetch_related('tenantuser_set')

@admin.register(TenantUser)
class TenantUserAdmin(admin.ModelAdmin):
    """Admin configuration for TenantUser model"""
    
    list_display = [
        'user', 
        'tenant', 
        'role_colored', 
        'created_at'
    ]
    list_filter = ['role', 'tenant', 'created_at']
    search_fields = ['user__username', 'user__email', 'tenant__name']
    readonly_fields = ['id', 'created_at']
    ordering = ['-created_at']
    autocomplete_fields = ['user', 'tenant']
    
    fieldsets = (
        ('User Information', {
            'fields': ('id', 'user', 'tenant', 'role')
        }),
        ('Timestamps', {
            'fields': ('created_at',),
            'classes': ('collapse',)
        }),
    )
    
    def role_colored(self, obj):
        """Display role with color coding"""
        colors = {
            'admin': 'red',
            'recruiter': 'blue',
            'viewer': 'green',
        }
        color = colors.get(obj.role, 'black')
        return format_html(
            '<span style="color: {}; font-weight: bold;">{}</span>',
            color,
            obj.get_role_display()
        )
    role_colored.short_description = 'Role'
    
    def get_queryset(self, request):
        """Optimize query with select_related"""
        return super().get_queryset(request).select_related('user', 'tenant')