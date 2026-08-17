from django.db.models.signals import post_save, pre_delete
from django.dispatch import receiver
from django.contrib.auth.models import User
from .models import Tenant, TenantUser
from apps.audit.services import AuditService

@receiver(post_save, sender=Tenant)
def audit_tenant_creation(sender, instance, created, **kwargs):
    """Audit tenant creation"""
    if created:
        # This is a system-level event, no actor available
        pass

@receiver(post_save, sender=TenantUser)
def audit_tenant_user(sender, instance, created, **kwargs):
    """Audit tenant user changes"""
    if created:
        # Log user added to tenant
        AuditService.log_create(
            tenant_id=str(instance.tenant.id),
            actor_id=instance.user.id,
            record_type='tenant_user',
            record_id=str(instance.id),
            data={
                'user_id': str(instance.user.id),
                'username': instance.user.username,
                'role': instance.role,
                'tenant_id': str(instance.tenant.id),
                'tenant_name': instance.tenant.name
            }
        )

@receiver(pre_delete, sender=TenantUser)
def audit_tenant_user_delete(sender, instance, **kwargs):
    """Audit tenant user removal"""
    AuditService.log_delete(
        tenant_id=str(instance.tenant.id),
        actor_id=instance.user.id,
        record_type='tenant_user',
        record_id=str(instance.id),
        data={
            'user_id': str(instance.user.id),
            'username': instance.user.username,
            'role': instance.role,
            'tenant_id': str(instance.tenant.id),
            'tenant_name': instance.tenant.name
        }
    )