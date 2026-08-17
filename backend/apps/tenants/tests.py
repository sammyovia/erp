from django.test import TestCase
from django.contrib.auth.models import User
from django.urls import reverse
from rest_framework.test import APITestCase, APIClient
from rest_framework import status
from .models import Tenant, TenantUser
import uuid

class TenantModelTest(TestCase):
    """Test Tenant model"""
    
    def setUp(self):
        self.tenant = Tenant.objects.create(
            name="Test Tenant",
            slug="test-tenant"
        )
        self.user = User.objects.create_user(
            username="testuser",
            password="testpass123"
        )
    
    def test_tenant_creation(self):
        """Test creating a tenant"""
        self.assertEqual(self.tenant.name, "Test Tenant")
        self.assertEqual(self.tenant.slug, "test-tenant")
        self.assertTrue(self.tenant.is_active)
        self.assertIsNotNone(self.tenant.id)
    
    def test_tenant_str(self):
        """Test tenant string representation"""
        self.assertEqual(str(self.tenant), "Test Tenant")
    
    def test_user_count(self):
        """Test user count property"""
        self.assertEqual(self.tenant.user_count, 0)
        
        # Add user to tenant
        TenantUser.objects.create(
            user=self.user,
            tenant=self.tenant,
            role='admin'
        )
        self.assertEqual(self.tenant.user_count, 1)

class TenantUserModelTest(TestCase):
    """Test TenantUser model"""
    
    def setUp(self):
        self.tenant = Tenant.objects.create(
            name="Test Tenant",
            slug="test-tenant"
        )
        self.user = User.objects.create_user(
            username="testuser",
            password="testpass123"
        )
        self.tenant_user = TenantUser.objects.create(
            user=self.user,
            tenant=self.tenant,
            role='admin'
        )
    
    def test_tenant_user_creation(self):
        """Test creating a tenant user"""
        self.assertEqual(self.tenant_user.user, self.user)
        self.assertEqual(self.tenant_user.tenant, self.tenant)
        self.assertEqual(self.tenant_user.role, 'admin')
    
    def test_tenant_user_str(self):
        """Test tenant user string representation"""
        expected = f"testuser - Test Tenant (admin)"
        self.assertEqual(str(self.tenant_user), expected)
    
    def test_is_admin(self):
        """Test is_admin method"""
        self.assertTrue(self.tenant_user.is_admin())
    
    def test_is_recruiter(self):
        """Test is_recruiter method"""
        self.assertTrue(self.tenant_user.is_recruiter())

class TenantAPITest(APITestCase):
    """Test Tenant API endpoints"""
    
    def setUp(self):
        # Create tenant
        self.tenant = Tenant.objects.create(
            name="Test Tenant",
            slug="test-tenant"
        )
        
        # Create user
        self.user = User.objects.create_user(
            username="testuser",
            password="testpass123",
            email="test@example.com"
        )
        
        # Add user to tenant as admin
        self.tenant_user = TenantUser.objects.create(
            user=self.user,
            tenant=self.tenant,
            role='admin'
        )
        
        # Setup client
        self.client = APIClient()
        self.client.force_authenticate(user=self.user)
        self.client.defaults['HTTP_X_TENANT_ID'] = str(self.tenant.id)
    
    def test_list_tenants(self):
        """Test listing tenants"""
        url = reverse('tenant-list')
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data['results']), 1)
    
    def test_retrieve_tenant(self):
        """Test retrieving a tenant"""
        url = reverse('tenant-detail', args=[self.tenant.id])
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['name'], "Test Tenant")
    
    def test_create_tenant(self):
        """Test creating a tenant"""
        url = reverse('tenant-list')
        data = {
            'name': 'New Tenant',
            'slug': 'new-tenant'
        }
        response = self.client.post(url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(response.data['name'], 'New Tenant')
        
        # Check that user was added as admin
        new_tenant = Tenant.objects.get(slug='new-tenant')
        self.assertTrue(TenantUser.objects.filter(
            user=self.user,
            tenant=new_tenant,
            role='admin'
        ).exists())
    
    def test_tenant_users(self):
        """Test getting tenant users"""
        url = reverse('tenant-users', args=[self.tenant.id])
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data['results']), 1)
        self.assertEqual(response.data['results'][0]['username'], 'testuser')
    
    def test_add_user_to_tenant(self):
        """Test adding a user to a tenant"""
        # Create a new user
        new_user = User.objects.create_user(
            username="newuser",
            password="newpass123"
        )
        
        url = reverse('tenant-add-user', args=[self.tenant.id])
        data = {
            'username': 'newuser',
            'role': 'viewer'
        }
        response = self.client.post(url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(response.data['username'], 'newuser')
        self.assertEqual(response.data['role'], 'viewer')
    
    def test_switch_tenant(self):
        """Test switching tenants"""
        # Create a second tenant
        tenant2 = Tenant.objects.create(
            name="Second Tenant",
            slug="second-tenant"
        )
        TenantUser.objects.create(
            user=self.user,
            tenant=tenant2,
            role='viewer'
        )
        
        url = reverse('tenant-switch')
        data = {'tenant_id': str(tenant2.id)}
        response = self.client.post(url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['tenant']['name'], "Second Tenant")
        self.assertIn('access', response.data)
        self.assertIn('refresh', response.data)
    
    def test_my_tenants(self):
        """Test getting user's tenants"""
        url = reverse('tenant-my-tenants')
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 1)
        self.assertEqual(response.data[0]['name'], "Test Tenant")