from django.contrib.auth.tokens import default_token_generator
from django.utils.http import urlsafe_base64_encode
from django.utils.encoding import force_bytes


def generate_verification_token(user):
    """
    Generate a verification token for email verification.
    
    Args:
        user: The user object to generate token for
        
    Returns:
        dict: Contains uid and token for verification URL
    """
    uid = urlsafe_base64_encode(force_bytes(user.pk))
    token = default_token_generator.make_token(user)
    
    return {
        'uid': uid,
        'token': token
    }
