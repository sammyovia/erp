from django.contrib import admin
from django.urls import reverse
from django.utils.html import format_html
from .models import Candidate

@admin.register(Candidate)
class CandidateAdmin(admin.ModelAdmin):
    """Admin configuration for Candidate model"""
    
    list_display = [
        'name', 
        'email', 
        'tenant', 
        'role_applied_for', 
        'document_count_display', 
        'created_at'
    ]
    list_filter = ['tenant', 'role_applied_for', 'is_active', 'created_at']
    search_fields = ['name', 'email', 'role_applied_for']
    readonly_fields = ['id', 'created_at', 'updated_at']
    ordering = ['-created_at']
    autocomplete_fields = ['tenant']
    
    fieldsets = (
        ('Basic Information', {
            'fields': ('id', 'tenant', 'name', 'email', 'role_applied_for')
        }),
        ('Status', {
            'fields': ('is_active',)
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )
    
    def document_count_display(self, obj):
        """Display document count with link"""
        count = obj.document_count
        if count > 0:
            url = reverse('admin:documents_compliancedocument_changelist') + f'?candidate__id__exact={obj.id}'
            return format_html('<a href="{}">{}</a>', url, count)
        return "0"
    document_count_display.short_description = 'Documents'
    
    def get_queryset(self, request):
        """Optimize query with prefetch"""
        qs = super().get_queryset(request)
        return qs.prefetch_related('documents', 'tenant')