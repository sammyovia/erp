from django.contrib import admin
from .models import ComplianceDocument

@admin.register(ComplianceDocument)
class ComplianceDocumentAdmin(admin.ModelAdmin):
    """Admin configuration for ComplianceDocument"""
    
    list_display = [
        'id',
        'candidate',
        'document_type',
        'status',
        'version',
        'is_current',
        'expiry_date',
        'created_at'
    ]
    list_filter = ['document_type', 'status', 'is_current', 'created_at']
    search_fields = ['candidate__name', 'candidate__email']
    readonly_fields = ['id', 'version', 'created_at', 'updated_at']
    ordering = ['-created_at']
    
    fieldsets = (
        ('Document Information', {
            'fields': ('id', 'candidate', 'document_type', 'status')
        }),
        ('Dates', {
            'fields': ('issue_date', 'expiry_date', 'verified_at')
        }),
        ('Versioning', {
            'fields': ('version', 'is_current', 'superseded_by')
        }),
        ('Verification', {
            'fields': ('verified_by',)
        }),
        ('File', {
            'fields': ('file_url',)
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )