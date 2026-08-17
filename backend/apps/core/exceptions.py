from rest_framework.views import exception_handler
from rest_framework.response import Response
from rest_framework import status
from django.core.exceptions import ValidationError
from django.db import IntegrityError

def custom_exception_handler(exc, context):
    """
    Custom exception handler for consistent error responses.
    Follows RFC 7807: Problem Details for HTTP APIs.
    """
    # Call REST framework's default exception handler first
    response = exception_handler(exc, context)
    
    # If response is None, Django raised an exception we didn't handle
    if response is None:
        if isinstance(exc, ValidationError):
            return Response({
                'type': 'validation_error',
                'title': 'Validation Error',
                'status': 400,
                'detail': str(exc),
                'errors': exc.message_dict if hasattr(exc, 'message_dict') else str(exc)
            }, status=status.HTTP_400_BAD_REQUEST)
        
        if isinstance(exc, IntegrityError):
            return Response({
                'type': 'integrity_error',
                'title': 'Integrity Error',
                'status': 400,
                'detail': 'Database integrity constraint violated'
            }, status=status.HTTP_400_BAD_REQUEST)
        
        return Response({
            'type': 'server_error',
            'title': 'Internal Server Error',
            'status': 500,
            'detail': 'An unexpected error occurred'
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
    
    # Customize the response format
    if response is not None:
        # Add type and title to the response
        status_code = response.status_code
        error_messages = {
            400: 'Bad Request',
            401: 'Unauthorized',
            403: 'Forbidden',
            404: 'Not Found',
            405: 'Method Not Allowed',
            500: 'Internal Server Error'
        }
        
        response.data['type'] = 'about:blank'
        response.data['title'] = error_messages.get(status_code, 'Error')
        response.data['status'] = status_code
        
        # If detail is missing, add it
        if 'detail' not in response.data:
            response.data['detail'] = str(exc)
    
    return response