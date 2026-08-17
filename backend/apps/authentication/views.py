from rest_framework import status
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView
from django.contrib.auth.models import User
from django.contrib.auth import authenticate
from rest_framework_simplejwt.tokens import RefreshToken
from rest_framework_simplejwt.exceptions import TokenError
from apps.tenants.models import Tenant, TenantUser

class RegisterView(APIView):
    """
    User registration endpoint with tenant creation
    """
    permission_classes = [AllowAny]
    
    def post(self, request):
        username = request.data.get('username')
        email = request.data.get('email')
        password = request.data.get('password')
        tenant_name = request.data.get('tenant_name')
        tenant_slug = request.data.get('tenant_slug')
        role = request.data.get('role', 'admin')
        
        # Validate required fields
        if not all([username, email, password, tenant_name, tenant_slug]):
            return Response(
                {
                    'error': 'Missing required fields',
                    'required_fields': ['username', 'email', 'password', 'tenant_name', 'tenant_slug']
                },
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # Check if user already exists
        if User.objects.filter(username=username).exists():
            return Response(
                {'error': 'Username already exists'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        if User.objects.filter(email=email).exists():
            return Response(
                {'error': 'Email already registered'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # Create tenant
        tenant, created = Tenant.objects.get_or_create(
            slug=tenant_slug,
            defaults={'name': tenant_name}
        )
        
        # Create user
        user = User.objects.create_user(
            username=username,
            email=email,
            password=password
        )
        
        # Link user to tenant
        TenantUser.objects.create(
            user=user,
            tenant=tenant,
            role=role
        )
        
        # Generate tokens
        refresh = RefreshToken.for_user(user)
        
        return Response({
            'access': str(refresh.access_token),
            'refresh': str(refresh),
            'user': {
                'id': user.id,
                'username': user.username,
                'email': user.email,
                'first_name': user.first_name,
                'last_name': user.last_name,
                'tenant_id': str(tenant.id),
                'tenant_name': tenant.name,
                'tenant_slug': tenant.slug,
                'role': role
            },
            'message': 'User registered successfully'
        }, status=status.HTTP_201_CREATED)

class LoginView(APIView):
    """
    User login endpoint with JWT token generation
    """
    permission_classes = [AllowAny]
    
    def post(self, request):
        username = request.data.get('username')
        password = request.data.get('password')
        tenant_id = request.data.get('tenant_id')
        
        if not username or not password:
            return Response(
                {'error': 'Username and password are required'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # Authenticate user
        user = authenticate(username=username, password=password)
        if not user:
            return Response(
                {'error': 'Invalid credentials'},
                status=status.HTTP_401_UNAUTHORIZED
            )
        
        # Verify tenant access
        tenant_user = None
        if tenant_id:
            try:
                tenant_user = TenantUser.objects.get(user=user, tenant_id=tenant_id)
            except TenantUser.DoesNotExist:
                return Response(
                    {'error': 'No access to this tenant'},
                    status=status.HTTP_403_FORBIDDEN
                )
        else:
            # Get first tenant if not specified
            tenant_user = TenantUser.objects.filter(user=user).first()
            if not tenant_user:
                return Response(
                    {'error': 'No tenant access. Please specify tenant_id'},
                    status=status.HTTP_403_FORBIDDEN
                )
        
        # Generate tokens
        refresh = RefreshToken.for_user(user)
        
        # Add custom claims to access token
        refresh.access_token['tenant_id'] = str(tenant_user.tenant.id)
        refresh.access_token['role'] = tenant_user.role
        refresh.access_token['tenant_slug'] = tenant_user.tenant.slug
        
        return Response({
            'access': str(refresh.access_token),
            'refresh': str(refresh),
            'user': {
                'id': user.id,
                'username': user.username,
                'email': user.email,
                'first_name': user.first_name,
                'last_name': user.last_name,
                'tenant_id': str(tenant_user.tenant.id),
                'tenant_name': tenant_user.tenant.name,
                'tenant_slug': tenant_user.tenant.slug,
                'role': tenant_user.role
            },
            'message': 'Login successful'
        }, status=status.HTTP_200_OK)

class LogoutView(APIView):
    """
    Logout view that blacklists the refresh token
    """
    permission_classes = [IsAuthenticated]
    
    def post(self, request):
        try:
            refresh_token = request.data.get('refresh')
            
            if not refresh_token:
                return Response(
                    {'error': 'Refresh token is required'},
                    status=status.HTTP_400_BAD_REQUEST
                )
            
            # Blacklist the refresh token
            token = RefreshToken(refresh_token)
            token.blacklist()
            
            return Response({
                'message': 'Successfully logged out',
                'status': 'success'
            }, status=status.HTTP_200_OK)
            
        except TokenError as e:
            return Response(
                {'error': f'Invalid token: {str(e)}'},
                status=status.HTTP_400_BAD_REQUEST
            )
        except Exception as e:
            return Response(
                {'error': f'Logout failed: {str(e)}'},
                status=status.HTTP_400_BAD_REQUEST
            )

class TokenRefreshView(APIView):
    """
    Custom token refresh view
    """
    permission_classes = [AllowAny]
    
    def post(self, request):
        refresh_token = request.data.get('refresh')
        
        if not refresh_token:
            return Response(
                {'error': 'Refresh token is required'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        try:
            token = RefreshToken(refresh_token)
            
            # Get user from token
            user_id = token.payload.get('user_id')
            user = User.objects.get(id=user_id)
            
            # Generate new tokens
            new_refresh = RefreshToken.for_user(user)
            
            # Copy tenant info to new token
            if 'tenant_id' in token.payload:
                new_refresh.access_token['tenant_id'] = token.payload['tenant_id']
            if 'role' in token.payload:
                new_refresh.access_token['role'] = token.payload['role']
            
            return Response({
                'access': str(new_refresh.access_token),
                'refresh': str(new_refresh),
                'message': 'Token refreshed successfully'
            }, status=status.HTTP_200_OK)
            
        except TokenError as e:
            return Response(
                {'error': f'Invalid refresh token: {str(e)}'},
                status=status.HTTP_400_BAD_REQUEST
            )
        except User.DoesNotExist:
            return Response(
                {'error': 'User not found'},
                status=status.HTTP_404_NOT_FOUND
            )
        except Exception as e:
            return Response(
                {'error': f'Token refresh failed: {str(e)}'},
                status=status.HTTP_400_BAD_REQUEST
            )

class TokenVerifyView(APIView):
    """
    Verify if a token is valid
    """
    permission_classes = [AllowAny]
    
    def post(self, request):
        token = request.data.get('token')
        
        if not token:
            return Response(
                {'error': 'Token is required'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        try:
            from rest_framework_simplejwt.tokens import AccessToken
            access_token = AccessToken(token)
            
            # Get user from token
            user_id = access_token.payload.get('user_id')
            user = User.objects.get(id=user_id)
            
            return Response({
                'valid': True,
                'user_id': user_id,
                'username': user.username,
                'email': user.email,
                'tenant_id': access_token.payload.get('tenant_id'),
                'role': access_token.payload.get('role'),
                'message': 'Token is valid'
            }, status=status.HTTP_200_OK)
            
        except TokenError as e:
            return Response({
                'valid': False,
                'error': f'Invalid token: {str(e)}'
            }, status=status.HTTP_401_UNAUTHORIZED)
        except User.DoesNotExist:
            return Response({
                'valid': False,
                'error': 'User not found'
            }, status=status.HTTP_404_NOT_FOUND)
        except Exception as e:
            return Response({
                'valid': False,
                'error': f'Verification failed: {str(e)}'
            }, status=status.HTTP_400_BAD_REQUEST)

class UserProfileView(APIView):
    """
    Get current user profile
    """
    permission_classes = [IsAuthenticated]
    
    def get(self, request):
        user = request.user
        tenant_id = getattr(request, 'tenant_id', None)
        
        # Get tenant info
        tenant_user = None
        if tenant_id:
            try:
                tenant_user = TenantUser.objects.get(user=user, tenant_id=tenant_id)
            except TenantUser.DoesNotExist:
                pass
        
        return Response({
            'id': user.id,
            'username': user.username,
            'email': user.email,
            'first_name': user.first_name,
            'last_name': user.last_name,
            'date_joined': user.date_joined,
            'last_login': user.last_login,
            'tenant': {
                'id': str(tenant_user.tenant.id) if tenant_user else None,
                'name': tenant_user.tenant.name if tenant_user else None,
                'slug': tenant_user.tenant.slug if tenant_user else None,
                'role': tenant_user.role if tenant_user else None
            } if tenant_user else None
        }, status=status.HTTP_200_OK)

class ChangePasswordView(APIView):
    """
    Change user password
    """
    permission_classes = [IsAuthenticated]
    
    def post(self, request):
        old_password = request.data.get('old_password')
        new_password = request.data.get('new_password')
        confirm_password = request.data.get('confirm_password')
        
        if not all([old_password, new_password, confirm_password]):
            return Response(
                {'error': 'All password fields are required'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        if new_password != confirm_password:
            return Response(
                {'error': 'New passwords do not match'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        user = request.user
        
        # Check old password
        if not user.check_password(old_password):
            return Response(
                {'error': 'Old password is incorrect'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # Set new password
        user.set_password(new_password)
        user.save()
        
        return Response({
            'message': 'Password changed successfully',
            'status': 'success'
        }, status=status.HTTP_200_OK)