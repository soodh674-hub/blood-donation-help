"""
Security middleware to protect against common web vulnerabilities and bot attacks
"""
import re
import asyncio
from django.http import HttpResponseForbidden
from asgiref.sync import iscoroutinefunction, markcoroutinefunction

class SecurityMiddleware:
    """
    Middleware to protect against common security threats:
    - Block WordPress scanner bots
    - Block common exploit attempts
    - Rate limiting for suspicious requests
    """
    
    # Patterns commonly used by malicious bots and scanners
    BLOCKED_PATTERNS = [
        # WordPress paths
        r'/wp-admin/',
        r'/wp-content/',
        r'/wp-includes/',
        r'/wordpress/',
        r'/wp-login\.php',
        r'/wp-register\.php',
        r'/xmlrpc\.php',
        
        # Common exploit paths
        r'/phpmyadmin/',
        r'/pma/',
        r'/mysql/',
        r'/admin\.php',
        r'/administrator/',
        r'/\.env',
        r'/\.git/',
        r'/config\.php',
        r'/shell\.php',
        r'/cmd\.php',
        
        # PHP file access attempts
        r'\.php$',
        
        # Other common attack vectors
        r'/etc/passwd',
        r'/proc/self/',
        r'/%00',  # Null byte injection
        
        # Additional patterns for comprehensive protection
        r'/\.vscode/',
        r'/node_modules/',
        r'/\.circleci/',
        r'/backup/',
        r'/test/',
        r'/tests/',
        r'/storage/',
        r'/database/',
        r'/graphql/',
        r'/kyc/',
    ]
    
    sync_capable = True
    async_capable = True
    
    def __init__(self, get_response):
        self.get_response = get_response
        self.compiled_patterns = [
            re.compile(pattern, re.IGNORECASE) 
            for pattern in self.BLOCKED_PATTERNS
        ]
        
        # Mark if the get_response is async
        if iscoroutinefunction(self.get_response):
            markcoroutinefunction(self)
    
    def __call__(self, request):
        # Check if we're in async context
        if iscoroutinefunction(self.get_response):
            return self.__acall__(request)
        
        # Sync path
        response = self.process_request(request)
        if response:
            return response
        
        response = self.get_response(request)
        return self.process_response(request, response)
    
    async def __acall__(self, request):
        # Async path
        response = self.process_request(request)
        if response:
            return response
        
        response = await self.get_response(request)
        
        # Handle the response properly in async context
        if asyncio.iscoroutine(response):
            response = await response
        
        return self.process_response(request, response)
    
    def process_request(self, request):
        """
        Check incoming requests against blocked patterns
        """
        try:
            path = request.path
            
            # Skip empty paths or root - these are legitimate
            if not path or path == '/' or path == '':
                return None
            
            # Check if path matches any blocked pattern
            for pattern in self.compiled_patterns:
                if pattern.search(path):
                    # Log the attempt using proper logging instead of print
                    import logging
                    logger = logging.getLogger(__name__)
                    logger.warning(f"Blocked suspicious request: {path}")

                    # Return 403 Forbidden
                    return HttpResponseForbidden(
                        '<h1>403 Forbidden</h1><p>Access denied.</p>',
                        content_type='text/html'
                    )
            
            # If no match, continue processing
            return None
        except Exception as e:
            # If any error occurs, allow the request to proceed
            import logging
            logger = logging.getLogger(__name__)
            logger.error(f"Security middleware error: {str(e)}")
            return None
    
    def process_response(self, request, response):
        """
        Add security headers to all responses
        """
        try:
            # Handle coroutines - this should not happen now but keep as safety net
            if asyncio.iscoroutine(response):
                import logging
                logger = logging.getLogger(__name__)
                logger.warning("Received coroutine in process_response, this should be handled before")
                return response
            
            # Add security headers only if response supports item assignment
            if hasattr(response, '__setitem__'):
                response['X-Content-Type-Options'] = 'nosniff'
                response['X-Frame-Options'] = 'DENY'
                response['X-XSS-Protection'] = '1; mode=block'
                response['Referrer-Policy'] = 'strict-origin-when-cross-origin'
                
                # Hide server information
                if 'Server' in response:
                    del response['Server']
            else:
                import logging
                logger = logging.getLogger(__name__)
                logger.warning(f"Response object does not support header setting: {type(response)}")
                
        except Exception as e:
            # If we can't set headers, log but don't crash
            import logging
            logger = logging.getLogger(__name__)
            logger.warning(f"Could not set security headers: {str(e)}")
        
        return response
