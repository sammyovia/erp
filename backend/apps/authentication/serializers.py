from rest_framework import serializers
from django.contrib.auth.models import User
from django.contrib.auth.password_validation import validate_password
from apps.tenants.models import TenantUser

class UserSerializer(serializers.ModelSerializer):
    """Serializer for User model"""
    
    role = serializers.SerializerMethodField()
    tenant_id = serializers.SerializerMethodField()
    tenant_name = serializers.SerializerMethodField()
    tenant_slug = serializers.SerializerMethodField()
    
    class Meta:
        model = User
        fields = [
            'id', 
            'username', 
            'email', 
            'first_name', 
            'last_name',
            'role',
            'tenant_id',
            'tenant_name',
            'tenant_slug',
            'date_joined',
            'last_login'
        ]
        read_only_fields = ['id', 'date_joined', 'last_login']
    
    def get_role(self, obj):
        """Get user's role for current tenant"""
        request = self.context.get('request')
        if request and hasattr(request, 'tenant_id'):
            try:
                tenant_user = TenantUser.objects.get(
                    user=obj,
                    tenant_id=request.tenant_id
                )
                return tenant_user.role
            except TenantUser.DoesNotExist:
                return None
        return None
    
    def get_tenant_id(self, obj):
        """Get user's tenant ID"""
        request = self.context.get('request')
        if request and hasattr(request, 'tenant_id'):
            return str(request.tenant_id)
        return None
    
    def get_tenant_name(self, obj):
        """Get user's tenant name"""
        request = self.context.get('request')
        if request and hasattr(request, 'tenant_id'):
            try:
                tenant_user = TenantUser.objects.get(
                    user=obj,
                    tenant_id=request.tenant_id
                )
                return tenant_user.tenant.name
            except TenantUser.DoesNotExist:
                return None
        return None
    
    def get_tenant_slug(self, obj):
        """Get user's tenant slug"""
        request = self.context.get('request')
        if request and hasattr(request, 'tenant_id'):
            try:
                tenant_user = TenantUser.objects.get(
                    user=obj,
                    tenant_id=request.tenant_id
                )
                return tenant_user.tenant.slug
            except TenantUser.DoesNotExist:
                return None
        return None

class RegisterSerializer(serializers.Serializer):
    """Serializer for user registration"""
    
    username = serializers.CharField(max_length=150)
    email = serializers.EmailField()
    password = serializers.CharField(write_only=True, validators=[validate_password])
    first_name = serializers.CharField(max_length=150, required=False)
    last_name = serializers.CharField(max_length=150, required=False)
    tenant_name = serializers.CharField(max_length=200)
    tenant_slug = serializers.SlugField(max_length=200)
    role = serializers.ChoiceField(choices=['admin', 'recruiter', 'viewer'], default='admin')
    
    def validate_username(self, value):
        if User.objects.filter(username=value).exists():
            raise serializers.ValidationError("Username already exists")
        return value
    
    def validate_email(self, value):
        if User.objects.filter(email=value).exists():
            raise serializers.ValidationError("Email already registered")
        return value

class LoginSerializer(serializers.Serializer):
    """Serializer for user login"""
    
    username = serializers.CharField(max_length=150)
    password = serializers.CharField(write_only=True)
    tenant_id = serializers.CharField(required=False)

class LogoutSerializer(serializers.Serializer):
    """Serializer for logout"""
    
    refresh = serializers.CharField(required=True)

class ChangePasswordSerializer(serializers.Serializer):
    """Serializer for changing password"""
    
    old_password = serializers.CharField(write_only=True)
    new_password = serializers.CharField(write_only=True, validators=[validate_password])
    confirm_password = serializers.CharField(write_only=True)
    
    def validate(self, data):
        if data['new_password'] != data['confirm_password']:
            raise serializers.ValidationError("New passwords do not match")
        return data