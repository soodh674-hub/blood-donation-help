from rest_framework import generics, status
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response
from rest_framework_simplejwt.views import TokenObtainPairView
from django.contrib.auth import get_user_model, authenticate, login, logout
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.core.mail import send_mail
from django.conf import settings
from django.shortcuts import render, redirect, get_object_or_404
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_POST
from django.db import connection, models
from django.http import JsonResponse
from django.core.files.storage import default_storage
from .serializers import (
    UserSerializer, UserUpdateSerializer, UserPublicSerializer,
    CustomTokenObtainPairSerializer, EmailVerificationSerializer,
    PasswordResetRequestSerializer, OTPVerificationSerializer, PasswordResetSerializer
)
from .models import User, PasswordResetOTP, DonorProfile, FavoriteDonor, Follow
from . import services as otp_services
from .tasks import send_password_reset_email_task
import random
import string
import logging
from django.core.cache import cache
from django.utils import timezone
from datetime import timedelta

# Setup logging
logger = logging.getLogger(__name__)

# Import logging configuration
# (Logging is configured globally in Django settings)

class CustomTokenObtainPairView(TokenObtainPairView):
    """Custom JWT token view"""
    serializer_class = CustomTokenObtainPairSerializer

class RegisterView(generics.CreateAPIView):
    """User registration endpoint"""
    queryset = User.objects.all()
    serializer_class = UserSerializer
    permission_classes = [AllowAny]
    
    def perform_create(self, serializer):
        user = serializer.save()
        # Send verification email (in production, use Celery)
        send_verification_email(user)
    
    def create(self, request, *args, **kwargs):
        # Log the incoming data for debugging
        logger.info(f"Registration attempt with data: {request.data}")
        
        # Override create to customize response
        serializer = self.get_serializer(data=request.data)
        if not serializer.is_valid():
            logger.error(f"Registration validation errors: {serializer.errors}")
            return Response(
                serializer.errors,
                status=status.HTTP_400_BAD_REQUEST
            )
        
        self.perform_create(serializer)
        headers = self.get_success_headers(serializer.data)
        
        # Return success response with user data
        return Response(
            {
                'message': 'User registered successfully',
                'user': serializer.data
            }, 
            status=status.HTTP_201_CREATED, 
            headers=headers
        )

class ProfileView(generics.RetrieveUpdateAPIView):
    """User profile endpoint"""
    serializer_class = UserUpdateSerializer
    permission_classes = [IsAuthenticated]
    
    def get_object(self):
        return self.request.user


class PublicProfileView(generics.RetrieveAPIView):
    """Public user profile view (privacy-controlled)"""
    queryset = User.objects.filter(privacy_level='public')
    serializer_class = UserPublicSerializer
    permission_classes = [AllowAny]

@api_view(['POST'])
@permission_classes([AllowAny])
def verify_email(request):
    """Email verification endpoint"""
    serializer = EmailVerificationSerializer(data=request.data)
    if serializer.is_valid():
        email = serializer.validated_data['email']
        code = serializer.validated_data['verification_code']
        
        try:
            user = User.objects.get(email=email)
            # In production, verify against stored code
            if verify_code(user, code):
                user.is_verified = True
                user.save()
                return Response({'message': 'Email verified successfully'}, status=status.HTTP_200_OK)
            else:
                return Response({'error': 'Invalid verification code'}, status=status.HTTP_400_BAD_REQUEST)
        except User.DoesNotExist:
            return Response({'error': 'User not found'}, status=status.HTTP_404_NOT_FOUND)
    
    return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)







# Helper functions (implement properly in production)
def send_verification_email(user):
    """Send email verification"""
    try:
        code = ''.join(random.choices(string.digits, k=6))
        # Store code in cache with expiration
        subject = 'Verify your email - Blood Donation Platform'
        message = f'Your verification code is: {code}'
        
        # Use explicit Brevo backend connection
        from django.core.mail import get_connection
        connection = get_connection(
            backend='blood_donation.email_backend.BrevoAPIEmailBackend',
            fail_silently=False
        )
        
        send_mail(subject, message, settings.DEFAULT_FROM_EMAIL, [user.email], connection=connection)
        logger.info(f"Verification email sent to {user.email}")
        return True
    except Exception as e:
        logger.error(f"Failed to send verification email to {user.email}: {str(e)}")
        return False

def verify_code(user, code):
    """Verify email code"""
    # Check against stored code
    return True  # Simplified for example


@api_view(['POST', 'GET'])
@permission_classes([AllowAny])
@csrf_exempt  # Exempt CSRF for API endpoints (frontend handles this separately)
def forgot_password(request):
    """Request password reset - generates and sends OTP"""
    try:
        # Check if this is an API request (JSON) or direct browser access
        # Accessing API endpoint directly in browser causes issues, so redirect
        content_type = getattr(request, 'content_type', '')
        if request.method == 'GET':
            # If someone accesses this endpoint directly in browser with GET, redirect to frontend page
            from django.shortcuts import redirect
            return redirect('forgot_password')
            
        logger.info(f"Password reset request received: {request.data}")
        serializer = PasswordResetRequestSerializer(data=request.data)
        
        if not serializer.is_valid():
            logger.error(f"Password reset serializer errors: {serializer.errors}")
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
        
        email = serializer.validated_data['email']
        logger.info(f"Processing password reset for email: {email}")
        
        try:
            user = User.objects.get(email=email, is_active=True)
            logger.info(f"Found user: {user.username}")
            
            # Rate limiting: Check if user requested OTP recently
            last_otp = PasswordResetOTP.objects.filter(
                user=user, 
                created_at__gte=timezone.now() - timedelta(seconds=60)
            ).first()
            
            if last_otp:
                remaining_time = 60 - (timezone.now() - last_otp.created_at).seconds
                logger.warning(f"Rate limiting user {user.email}, {remaining_time} seconds remaining")
                return Response(
                    {'error': f'Please wait {remaining_time} seconds before requesting another OTP'},
                    status=status.HTTP_429_TOO_MANY_REQUESTS
                )
            
            # Generate new OTP
            logger.info(f"Generating OTP for user {user.email}")
            otp_record = PasswordResetOTP.generate_otp(user)
            otp = otp_record.otp
            logger.info(f"Generated OTP for {user.email}: {otp}")
            
            # Send email with OTP asynchronously to prevent worker timeout
            logger.info(f"Sending OTP email to {user.email}")
            
            # Import send_password_reset_email_direct to call it
            email_sent = False
            try:
                # Call the email function directly but with exception handling to prevent blocking
                email_sent = send_password_reset_email_direct(user, otp)
            except Exception as email_error:
                # Log the error but don't fail the request since email is non-critical
                logger.error(f"Non-blocking email error for {user.email}: {str(email_error)}")
            
            # If direct email sending fails, queue a Celery task as backup
            if not email_sent:
                try:
                    from .tasks import send_password_reset_email_task
                    send_password_reset_email_task.delay(user.email, user.first_name or user.username, otp)
                    logger.info(f"Queued Celery task for sending OTP email to {user.email}")
                except Exception as task_error:
                    logger.warning(f"Failed to queue Celery task for {user.email}: {str(task_error)}")
                    # Log as warning instead of error since this is a backup method
                    # and the main email delivery is handled directly in send_password_reset_email_direct
            
            logger.info(f"Password reset OTP processing completed for {user.email}. Email sent: {email_sent}")
            
            # Return success response regardless of email delivery status
            message = 'If email exists, OTP has been sent'
            if not email_sent:
                message += ' (Note: There may be a delay in email delivery or an issue with the email configuration)'
            
            return Response(
                {
                    'message': message,
                },
                status=status.HTTP_200_OK
            )
                
        except User.DoesNotExist:
            # For security, we don't reveal if email exists
            # But we log this for monitoring
            logger.info(f"Password reset requested for non-existent email: {email}")
            return Response(
                {'message': 'If email exists, OTP has been sent'},  # Generic message
                status=status.HTTP_200_OK
            )
            
    except Exception as e:
        logger.error(f"Unexpected error in forgot_password: {str(e)}", exc_info=True)
        return Response(
            {'error': 'An unexpected error occurred. Please try again later.'},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )


@api_view(['POST'])
@permission_classes([AllowAny])
def verify_otp(request):
    """Verify OTP for password reset"""
    try:
        # Handle direct browser access
        if request.method == 'GET':
            # If someone accesses this endpoint directly in browser with GET, redirect to frontend page
            from django.shortcuts import redirect
            return redirect('verify_otp')
        
        logger.info(f"OTP verification request received: {request.data}")
        serializer = OTPVerificationSerializer(data=request.data)
        
        if not serializer.is_valid():
            logger.error(f"OTP verification serializer errors: {serializer.errors}")
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
        
        email = serializer.validated_data['email']
        entered_otp = serializer.validated_data['otp']
        logger.info(f"Processing OTP verification for email: {email}")
        
        try:
            user = User.objects.get(email=email, is_active=True)
            logger.info(f"Found user for OTP verification: {user.username}")
            
            # Get the latest OTP for this user
            otp_record = PasswordResetOTP.objects.filter(
                user=user
            ).order_by('-created_at').first()
            
            if not otp_record:
                logger.warning(f"No OTP found for user {user.email}")
                return Response(
                    {'error': 'No OTP found for this email. Please request a new one.'},
                    status=status.HTTP_400_BAD_REQUEST
                )
            
            # Check if OTP is already verified
            if otp_record.is_verified:
                logger.warning(f"OTP already used for user {user.email}")
                return Response(
                    {'error': 'OTP already used. Please request a new one.'},
                    status=status.HTTP_400_BAD_REQUEST
                )
            
            # Verify OTP
            is_valid, message = otp_record.verify_otp(entered_otp)
            
            if is_valid:
                logger.info(f"OTP verified successfully for user {user.email}")
                return Response(
                    {'message': 'OTP verified successfully. You can now reset your password'},
                    status=status.HTTP_200_OK
                )
            else:
                logger.warning(f"OTP verification failed for {user.email}: {message}")
                return Response(
                    {'error': message},
                    status=status.HTTP_400_BAD_REQUEST
                )
                
        except User.DoesNotExist:
            logger.error(f"User not found for OTP verification: {email}")
            return Response(
                {'error': 'Invalid email address'},
                status=status.HTTP_400_BAD_REQUEST
            )
            
    except Exception as e:
        logger.error(f"Unexpected error in verify_otp: {str(e)}", exc_info=True)
        return Response(
            {'error': 'An unexpected error occurred. Please try again later.'},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )


@api_view(['POST'])
@permission_classes([AllowAny])
def reset_password(request):
    """Reset password after OTP verification"""
    try:
        # Handle direct browser access
        if request.method == 'GET':
            # If someone accesses this endpoint directly in browser with GET, redirect to frontend page
            from django.shortcuts import redirect
            return redirect('reset_password')
        
        logger.info(f"Password reset request received: {request.data}")
        serializer = PasswordResetSerializer(data=request.data)
        
        if not serializer.is_valid():
            logger.error(f"Password reset serializer errors: {serializer.errors}")
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
        
        email = serializer.validated_data['email']
        new_password = serializer.validated_data['new_password']
        
        # Get the user from the database
        try:
            user = User.objects.get(email=email, is_active=True)
        except User.DoesNotExist:
            logger.error(f"User not found for password reset: {email}")
            return Response(
                {'error': 'Invalid email address'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # Verify OTP: database-based verification
        verified_otp = PasswordResetOTP.objects.filter(
            user=user,
            is_verified=True
        ).order_by('-created_at').first()
        
        if not verified_otp or verified_otp.is_expired:
            logger.warning(f"No verified OTP found for user {user.email} or OTP has expired")
            return Response(
                {'error': 'OTP verification is required. Please start again.'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        logger.info(f"Processing password reset for user: {user.username}")
        
        try:
            # Update password
            user.set_password(new_password)
            user.save()
            
            # Clear OTP state (cache + DB)
            otp_services.clear_reset_state(user.id)
            PasswordResetOTP.objects.filter(user=user).delete()
            
            logger.info(f"Password reset successful for user {user.email}")
            
            return Response(
                {'message': 'Password reset successful. You can now login with your new password'},
                status=status.HTTP_200_OK
            )
            
        except Exception as e:
            logger.error(f"Password reset failed: {str(e)}")
            return Response(
                {'error': 'Failed to reset password. Please try again'},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
            
    except Exception as e:
        logger.error(f"Unexpected error in reset_password: {str(e)}", exc_info=True)
        return Response(
            {'error': 'An unexpected error occurred. Please try again later.'},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )

def send_password_reset_email_direct(user, otp):
    """Direct function to send password reset OTP email using Brevo HTTP API"""
    subject = 'Password Reset OTP - Blood Donation Platform'
    html_message = f'''
    <html>
    <body>
        <h2>Password Reset Request</h2>
        <p>Hello {user.first_name or user.username},</p>
        
        <p>You have requested to reset your password. Your One-Time Password (OTP) is:</p>
        
        <h1 style="color: #d32f2f; font-size: 2em;">{otp}</h1>
        
        <p><strong>This OTP will expire in 5 minutes.</strong></p>
        
        <p>If you did not request this password reset, please ignore this email.</p>
        
        <p>Best regards,<br>
        Blood Donation Platform Team</p>
    </body>
    </html>
    '''.strip()
    
    # Send email using Django's send_mail() which will use BrevoAPIEmailBackend
    try:
        from django.core.mail import send_mail, get_connection
        from django.conf import settings
        
        # Explicitly get the Brevo API email connection
        connection = get_connection(
            backend='blood_donation.email_backend.BrevoAPIEmailBackend',
            fail_silently=False
        )
        
        # send_mail() will use our custom backend via the connection parameter
        send_mail(
            subject=subject,
            message=html_message,  # HTML content
            from_email=settings.DEFAULT_FROM_EMAIL,
            recipient_list=[user.email],
            fail_silently=False,
            html_message=html_message,  # Explicitly pass HTML
            connection=connection  # Force use of Brevo backend
        )
        
        logger.info(f"✅ Email sent successfully to {user.email} via Brevo HTTP API")
        return True
        
    except Exception as e:
        logger.error(f"❌ Failed to send email to {user.email}: {str(e)}")
        logger.exception(e)  # Log full traceback for debugging
        return False

# Frontend view functions
def forgot_password_page(request):
    """Render forgot password page"""
    return render(request, 'accounts/forgot_password.html')

def verify_otp_page(request):
    """Render OTP verification page"""
    email = request.GET.get('email', '')
    if not email:
        messages.error(request, 'Email is required for OTP verification')
        return redirect('forgot_password')
    return render(request, 'accounts/verify_otp.html', {'email': email})


def reset_password_page(request):
    """Render reset password page"""
    email = request.GET.get('email', '')
    if not email:
        messages.error(request, 'Email is required for password reset')
        return redirect('forgot_password')
    
    # Verify there's a verified OTP for this email (cache or DB)
    try:
        user = User.objects.get(email=email, is_active=True)
        verified_in_cache = otp_services.is_otp_verified(user.id)
        verified_otp = PasswordResetOTP.objects.filter(
            user=user, is_verified=True
        ).order_by('-created_at').first()
        
        if not verified_in_cache and (not verified_otp or verified_otp.is_expired):
            messages.error(request, 'OTP verification is required. Please start again.')
            return redirect('forgot_password')
    except User.DoesNotExist:
        messages.error(request, 'Invalid user for password reset')
        return redirect('forgot_password')
    
    return render(request, 'accounts/reset_password.html', {'email': email})




def donor_registration_view(request):
    """Render the donor registration page with blood types"""
    from django.conf import settings
    
    # Create captcha form
    captcha_form = None
    if 'captcha' in settings.INSTALLED_APPS:
        try:
            from captcha.forms import CaptchaForm
            captcha_form = CaptchaForm()
        except (ImportError, Exception) as e:
            logger.debug(f"Captcha form not available: {e}")
    
    blood_types = ['A+', 'A-', 'B+', 'B-', 'AB+', 'AB-', 'O+', 'O-']
    return render(request, 'accounts/register_donor.html', {
        'blood_types': blood_types,
        'captcha_form': captcha_form
    })


def register_donor_view(request):
    """Handle donor registration via traditional Django form with comprehensive error handling"""
    from django.conf import settings
    
    # Check if captcha is available and import CaptchaForm
    has_captcha = 'captcha' in settings.INSTALLED_APPS
    CaptchaForm = None
    if has_captcha:
        try:
            from captcha.forms import CaptchaForm as CF
            CaptchaForm = CF
        except (ImportError, Exception) as e:
            logger.debug(f"Captcha form not available: {e}")
            has_captcha = False
    
    if request.method == 'POST':
        # Extract all form data
        username = request.POST.get('username', '').strip()
        email = request.POST.get('email', '').strip()
        password = request.POST.get('password', '').strip()
        confirm_password = request.POST.get('confirm_password', '').strip()
        first_name = request.POST.get('first_name', '').strip()
        last_name = request.POST.get('last_name', '').strip()
        phone_number = request.POST.get('phone_number', '').strip()
        blood_group = request.POST.get('blood_group', '').strip()
        date_of_birth = request.POST.get('date_of_birth', '').strip()
        city = request.POST.get('city', '').strip()
        state = request.POST.get('state', '').strip()
        country = request.POST.get('country', 'India').strip()
        pincode = request.POST.get('pincode', '').strip()
        user_type = request.POST.get('user_type', 'donor').strip()
        consent_given = request.POST.get('consent_given') == 'on'
        data_retention_consent = request.POST.get('data_retention_consent') == 'on'
        
        # CAPTCHA validation
        captcha_response = request.POST.get('captcha_0', '')
        captcha_key = request.POST.get('captcha_1', '')
        
        # Comprehensive validation
        errors = {}
        
        # Required field validation
        if not username:
            errors['username'] = ['Username is required.']
        elif len(username) < 3:
            errors['username'] = ['Username must be at least 3 characters long.']
            
        if not email:
            errors['email'] = ['Email is required.']
        elif '@' not in email:
            errors['email'] = ['Please enter a valid email address.']
            
        if not password:
            errors['password'] = ['Password is required.']
        elif len(password) < 8:
            errors['password'] = ['Password must be at least 8 characters long.']
        elif password != confirm_password:
            errors['confirm_password'] = ['Passwords do not match.']
        
        # CAPTCHA validation (only if captcha is available)
        if has_captcha and CaptchaForm:
            from captcha.models import CaptchaStore
            try:
                CaptchaStore.objects.get(hashkey=captcha_key).delete()
            except CaptchaStore.DoesNotExist:
                errors['captcha'] = ['Invalid CAPTCHA. Please try again.']
            except Exception as captcha_db_error:
                logger.warning(f'CAPTCHA database error: {str(captcha_db_error)}')
                # Continue without captcha if table doesn't exist
                pass
            
        # Check if username or email already exists
        User = get_user_model()
        if username and User.objects.filter(username=username).exists():
            errors['username'] = errors.get('username', []) + ['Username already exists.']
        
        if email and User.objects.filter(email=email).exists():
            errors['email'] = errors.get('email', []) + ['Email already exists.']

        # Age restriction validation - must be at least 18 years old
        if date_of_birth:
            try:
                from datetime import datetime
                dob = datetime.strptime(date_of_birth, '%Y-%m-%d').date()
                today = datetime.now().date()
                age = today.year - dob.year - ((today.month, today.day) < (dob.month, dob.day))

                if age < 18:
                    errors['date_of_birth'] = ['You must be at least 18 years old to register as a blood donor.']
                elif age > 100:
                    errors['date_of_birth'] = ['Please enter a valid date of birth.']
            except ValueError:
                errors['date_of_birth'] = ['Please enter a valid date of birth (YYYY-MM-DD).']
        else:
            errors['date_of_birth'] = ['Date of birth is required.']

        # If there are validation errors, return them
        if errors:
            messages.error(request, 'Please correct the errors below.')
            blood_types = ['A+', 'A-', 'B+', 'B-', 'AB+', 'AB-', 'O+', 'O-']
            captcha_form = CaptchaForm() if CaptchaForm else None
            return render(request, 'accounts/register_donor.html', {
                'blood_types': blood_types,
                'errors': errors,
                'form_data': request.POST,  # Preserve form data
                'captcha_form': captcha_form
            })
        
        try:
            # Create user with all provided data
            user = User.objects.create_user(
                username=username,
                email=email,
                password=password,
                first_name=first_name,
                last_name=last_name,
                user_type=user_type,
                phone_number=phone_number,
                blood_group=blood_group,
                date_of_birth=date_of_birth,
                city=city,
                state=state,
                country=country,
                pincode=pincode,
                consent_given=consent_given,
                data_retention_consent=data_retention_consent,
                is_active=True,  # Activate immediately
                is_verified=True  # Auto-verify for testing
            )
            
            # Log the user in automatically after registration
            login(request, user)
            
            # Create "Update Profile" notification for new users
            try:
                from notifications.models import Notification
                Notification.objects.create(
                    user=user,
                    notification_type='general',
                    title='🎉 Complete Your Profile!',
                    message='Welcome to BloodLife! Complete your profile to help us match you with blood requests in your area. Add your photo, location, and medical information.',
                    priority='high',
                    category='system'
                )
            except Exception as e:
                logger.error(f"Failed to create profile update notification: {str(e)}")
            
            messages.success(request, f'Registration successful! Welcome, {user.first_name or user.username}!')
            return redirect('/accounts/dashboard/')
            
        except Exception as e:
            logger.error(f'Registration error: {str(e)}', exc_info=True)
            messages.error(request, f'Registration failed: {str(e)}')
            blood_types = ['A+', 'A-', 'B+', 'B-', 'AB+', 'AB-', 'O+', 'O-']
            return render(request, 'accounts/register_donor.html', {
                'blood_types': blood_types,
                'errors': {'general': [f'Registration failed: {str(e)}']},
                'form_data': request.POST
            })
    
    # GET request - show registration form
    blood_types = ['A+', 'A-', 'B+', 'B-', 'AB+', 'AB-', 'O+', 'O-']
    captcha_form = CaptchaForm() if CaptchaForm else None
    return render(request, 'accounts/register_donor.html', {
        'blood_types': blood_types,
        'captcha_form': captcha_form
    })



def login_view(request):
    """Handle login page rendering and authentication"""
    # If user is already authenticated, redirect to dashboard
    if request.user.is_authenticated:
        return redirect('/accounts/dashboard/')

    # Check if captcha is available and import CaptchaForm
    has_captcha = 'captcha' in settings.INSTALLED_APPS
    CaptchaForm = None
    if has_captcha:
        try:
            from captcha.forms import CaptchaForm as CF
            CaptchaForm = CF
        except (ImportError, Exception) as e:
            logger.debug(f"Captcha form not available: {e}")
            has_captcha = False

    if request.method == 'POST':
        username = request.POST.get('username')
        password = request.POST.get('password')

        if not username or not password:
            messages.error(request, 'Please enter both username/email and password.')
            captcha_form = CaptchaForm() if CaptchaForm else None
            return render(request, 'accounts/login.html', {'captcha_form': captcha_form})

        # CAPTCHA validation (only if captcha is available)
        if has_captcha:
            captcha_response = request.POST.get('captcha_0', '')
            captcha_key = request.POST.get('captcha_1', '')

            if not captcha_response or not captcha_key:
                messages.error(request, 'Please complete the security verification.')
                captcha_form = CaptchaForm() if CaptchaForm else None
                return render(request, 'accounts/login.html', {'captcha_form': captcha_form})

            # Validate CAPTCHA
            from captcha.models import CaptchaStore
            try:
                CaptchaStore.objects.get(hashkey=captcha_key, response=captcha_response)
            except CaptchaStore.DoesNotExist:
                errors = {'captcha': ['Invalid CAPTCHA. Please try again.']}
                captcha_form = CaptchaForm() if CaptchaForm else None
                return render(request, 'accounts/login.html', {'captcha_form': captcha_form, 'errors': errors})
            except Exception as captcha_db_error:
                logger.warning(f'CAPTCHA database error in login: {str(captcha_db_error)}')
                # Continue without captcha if table doesn't exist
                pass

        # Handle both username and email login
        # Try authenticating with username first
        user = authenticate(request, username=username, password=password)

        # If that fails, try with email
        if user is None:
            User = get_user_model()
            try:
                user_obj = User.objects.get(email=username)
                user = authenticate(request, username=user_obj.username, password=password)
            except User.DoesNotExist:
                user = None
            except Exception as e:
                # Log the error for debugging
                logger.error(f'Login error: {str(e)}', exc_info=True)
                messages.error(request, 'An error occurred during login. Please try again.')
                captcha_form = CaptchaForm() if CaptchaForm else None
                return render(request, 'accounts/login.html', {'captcha_form': captcha_form})

        if user is not None:
            if user.is_active:
                login(request, user)
                messages.success(request, f'Welcome back, {user.first_name or user.username}!')
                # Redirect to dashboard or home page
                next_url = request.GET.get('next', '/accounts/dashboard/')
                return redirect(next_url)
            else:
                messages.error(request, 'Your account is inactive. Please contact support.')
        else:
            messages.error(request, 'Invalid username/email or password. Please try again.')

    # Create captcha form if enabled
    captcha_form = CaptchaForm() if CaptchaForm else None
    return render(request, 'accounts/login.html', {'captcha_form': captcha_form})


def logout_view(request):
    """Handle user logout"""
    logout(request)
    messages.success(request, 'You have been successfully logged out.')
    return redirect('/')


def donor_search_page(request):
    """Render the donor search page (public access)"""
    return render(request, 'search/donor_search.html')


@api_view(['PUT'])
@permission_classes([IsAuthenticated])
def update_profile(request):
    """API endpoint to update user profile"""
    user = request.user
    
    # Fields that can be updated
    updatable_fields = [
        'first_name', 'last_name', 'phone_number', 
        'blood_group', 'date_of_birth', 'city', 
        'state', 'country', 'pincode', 'is_available', 'last_donation_date'
    ]
    
    # Update fields
    for field in updatable_fields:
        if field in request.data:
            value = request.data[field]
            # Handle boolean conversion for is_available field
            if field == 'is_available':
                if isinstance(value, str):
                    # Convert string boolean to actual boolean
                    value = value.lower() in ['true', '1', 'yes', 'on']
                elif isinstance(value, bool):
                    # Already boolean, keep as is
                    pass
                else:
                    # Convert other types to boolean
                    value = bool(value)
            
            setattr(user, field, value)
    
    try:
        user.save()
        serializer = UserUpdateSerializer(user)  # Changed to use UserUpdateSerializer
            
        # Prepare response data
        response_data = {
            **serializer.data,
            'is_available': user.is_available,
        }
            
        # Handle last_donation_date - could be string or date object
        if user.last_donation_date:
            if hasattr(user.last_donation_date, 'isoformat'):
                # It's already a date object
                response_data['last_donation_date'] = user.last_donation_date.isoformat()
            else:
                # It's a string, return as-is
                response_data['last_donation_date'] = str(user.last_donation_date)
        else:
            response_data['last_donation_date'] = None
                
        # Add calculated field
        response_data['days_since_last_donation'] = user.days_since_last_donation
            
        return Response({
            'message': 'Profile updated successfully',
            'user': response_data
        }, status=status.HTTP_200_OK)
    except Exception as e:
        # Log the actual error for debugging
        logger.error(f'Profile update error: {str(e)}', exc_info=True)
        
        # Return user-friendly error message
        error_msg = str(e)
        if 'true" value must be either True or False' in error_msg:
            error_msg = 'Invalid availability status. Please select "Available for donation" or "Not available".'
        
        return Response({
            'error': f'Failed to update profile: {error_msg}'
        }, status=status.HTTP_400_BAD_REQUEST)

def profile_page(request):
    """Render user profile page"""
    if not request.user.is_authenticated:
        messages.error(request, 'Please login to view your profile.')
        return redirect('/accounts/login/')
    
    # Ensure user has all required attributes
    user = request.user
    return render(request, 'accounts/profile.html', {'user': user})


def near_me_page(request):
    """Render page to find users near the current user within 25km"""
    if not request.user.is_authenticated:
        messages.error(request, 'Please login to find users near you.')
        return redirect('/accounts/login/')
    
    from math import radians, cos, sin, asin, sqrt
    
    # Get user's location
    user_lat = request.user.latitude
    user_lng = request.user.longitude
    
    if not user_lat or not user_lng:
        messages.warning(request, 'Please set your location in your profile to find users near you.')
        return redirect('/accounts/settings/')
    
    # Find users within 25km
    nearby_users = []
    all_users = User.objects.filter(is_active=True).exclude(id=request.user.id)
    
    for user in all_users:
        if user.latitude and user.longitude:
            # Calculate distance using Haversine formula
            lat1, lon1 = radians(float(user_lat)), radians(float(user_lng))
            lat2, lon2 = radians(float(user.latitude)), radians(float(user.longitude))
            dlon = lon2 - lon1
            dlat = lat2 - lat1
            a = sin(dlat/2)**2 + cos(lat1) * cos(lat2) * sin(dlon/2)**2
            c = 2 * asin(sqrt(a))
            distance = c * 6371  # Earth's radius in km
            
            if distance <= 25:
                nearby_users.append({
                    'user': user,
                    'distance': round(distance, 2)
                })
    
    # Sort by distance
    nearby_users.sort(key=lambda x: x['distance'])
    
    return render(request, 'accounts/near_me.html', {
        'nearby_users': nearby_users,
        'total_count': len(nearby_users)
    })


def dashboard_page(request):
    """Render user dashboard page"""
    if not request.user.is_authenticated:
        messages.error(request, 'Please login to access your dashboard.')
        return redirect('/accounts/login/')
    
    # Get user statistics with error handling
    try:
        is_eligible = request.user.is_eligible_donor if hasattr(request.user, 'is_eligible_donor') else False
        days_since_donation = request.user.days_since_last_donation if hasattr(request.user, 'days_since_last_donation') else None
        can_donate = is_eligible and getattr(request.user, 'is_available', False)
        
        stats = {
            'is_eligible': is_eligible,
            'days_since_donation': days_since_donation,
            'can_donate': can_donate
        }
    except AttributeError as e:
        # Handle cases where user attributes might not be available
        stats = {
            'is_eligible': False,
            'days_since_donation': None,
            'can_donate': False
        }
    
    # Get profile completion data
    try:
        profile_completion = request.user.get_profile_completion()
    except:
        profile_completion = {'percentage': 0, 'completed': 0, 'total': 10, 'is_complete': False}
    
    # Check if there's an unread "Update Profile" notification
    has_update_profile_notification = False
    try:
        from notifications.models import Notification
        has_update_profile_notification = Notification.objects.filter(
            user=request.user,
            title__icontains='complete your profile',
            is_read=False
        ).exists()
    except:
        pass
    
    return render(request, 'accounts/dashboard.html', {
        'user': request.user,
        'stats': stats,
        'profile_completion': profile_completion,
        'show_progress_bar': not request.user.profile_completion_seen or has_update_profile_notification
    })


def user_search_page(request):
    """Render the user search page (public access)"""
    return render(request, 'search/user_search.html')


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def mark_profile_completion_seen(request):
    """Mark profile completion bar as seen by user"""
    try:
        request.user.profile_completion_seen = True
        request.user.save()
        
        # Also mark any "Update Profile" notifications as read
        try:
            from notifications.models import Notification
            Notification.objects.filter(
                user=request.user,
                title__icontains='complete your profile',
                is_read=False
            ).update(is_read=True)
        except:
            pass
        
        return Response({'success': True, 'message': 'Profile completion marked as seen'})
    except Exception as e:
        return Response({'error': str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@api_view(['GET'])
@permission_classes([AllowAny])  # Allow public access
def user_search_api(request):
    """API endpoint to search users by ID, name, or phone number"""
    try:
        query = request.query_params.get('query', '').strip()
        pincode = request.query_params.get('pincode', '').strip()
        
        if not query:
            return Response(
                {'error': 'Search query is required'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # Build search query
        users = User.objects.filter(is_active=True)
        
        # Search by ID (exact match)
        if query.isdigit():
            users = users.filter(id=int(query))
        else:
            # Search by name or phone (partial match)
            users = users.filter(
                models.Q(first_name__icontains=query) |
                models.Q(last_name__icontains=query) |
                models.Q(username__icontains=query) |
                models.Q(phone_number__icontains=query)
            )
        
        # Filter by pincode if provided
        if pincode:
            users = users.filter(pincode=pincode)
        
        # EXCLUDE users with anonymous_mode enabled (privacy feature)
        try:
            from .models import PrivacySettings
            anonymous_user_ids = PrivacySettings.objects.filter(
                anonymous_mode=True
            ).values_list('user_id', flat=True)
            users = users.exclude(id__in=anonymous_user_ids)
        except Exception as e:
            logger.warning(f'Could not filter anonymous users: {str(e)}')
        
        # Apply privacy filtering
        if not request.user.is_authenticated or not request.user.is_staff:
            # Non-admin users can only see public profiles
            users = users.filter(privacy_level='public')
            serializer_class = UserPublicSerializer
        else:
            # Admin users can see all user details
            from .serializers import UserSerializer
            serializer_class = UserSerializer
        
        # Serialize results
        serializer = serializer_class(users, many=True, context={'request': request})
        
        logger.info(f'User search completed: {len(users)} results for query "{query}"')
        
        return Response({
            'count': len(users),
            'results': serializer.data
        })
         
    except Exception as e:
        logger.error(f'User search error: {str(e)}', exc_info=True)
        return Response(
            {'error': 'An error occurred while searching for users'},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )


@api_view(['GET'])
@permission_classes([AllowAny])
def user_detail_api(request, user_id):
    """API endpoint to get user details by ID"""
    try:
        user = get_object_or_404(User, id=user_id, is_active=True)

        # Apply privacy filtering
        if not request.user.is_authenticated or not request.user.is_staff:
            # Non-admin users can only see public profiles
            if user.privacy_level != 'public':
                return Response(
                    {'error': 'User profile is private'},
                    status=status.HTTP_403_FORBIDDEN
                )
            serializer_class = UserPublicSerializer
        else:
            # Admin users can see all user details
            from .serializers import UserSerializer
            serializer_class = UserSerializer

        serializer = serializer_class(user, context={'request': request})

        logger.info(f'User detail retrieved for user ID: {user_id}')

        return Response(serializer.data)

    except User.DoesNotExist:
        return Response(
            {'error': 'User not found'},
            status=status.HTTP_404_NOT_FOUND
        )
    except Exception as e:
        logger.error(f'User detail error: {str(e)}', exc_info=True)
        return Response(
            {'error': 'An error occurred while fetching user details'},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )


def terms_of_service_page(request):
    """Render Terms of Service page"""
    from django.utils import timezone
    return render(request, 'legal/terms_of_service.html', {
        'current_date': timezone.now()
    })


def privacy_policy_page(request):
    """Render Privacy Policy page"""
    from django.utils import timezone
    return render(request, 'legal/privacy_policy.html', {
        'current_date': timezone.now()
    })


def settings_page(request):
    """User settings page with all preferences and account management"""
    if not request.user.is_authenticated:
        return redirect('/accounts/login/?next=/accounts/settings/')

    # Get user profile data
    user = request.user

    # Get or create notification settings
    from accounts.models import NotificationSettings, PrivacySettings
    try:
        notification_settings = user.notification_settings
    except NotificationSettings.DoesNotExist:
        notification_settings = NotificationSettings.objects.create(user=user)

    try:
        privacy_settings = user.privacy_settings
    except PrivacySettings.DoesNotExist:
        privacy_settings = PrivacySettings.objects.create(user=user)

    context = {
        'user': user,
        'full_name': user.get_full_name() or user.username,
        'email': user.email,
        'phone': getattr(user, 'phone_number', '') or '',
        'blood_group': getattr(user, 'blood_group', '') or '',
        'city': getattr(user, 'city', '') or '',
        'state': getattr(user, 'state', '') or '',
        'country': getattr(user, 'country', 'India'),
        'pincode': getattr(user, 'pincode', '') or '',
        'is_donor': getattr(user, 'is_donor', False),
        'last_donation_date': getattr(user, 'last_donation_date', None),
        # Notification settings
        'notification_settings': notification_settings,
        # Privacy settings
        'privacy_settings': privacy_settings,
    }

    return render(request, 'accounts/settings.html', context)


@api_view(['PUT'])
@permission_classes([IsAuthenticated])
def update_user_settings(request):
    """API endpoint to update user settings - comprehensive handler"""
    try:
        user = request.user
        data = request.data
        
        # Update basic user info
        if 'first_name' in data:
            user.first_name = data['first_name']
        if 'last_name' in data:
            user.last_name = data['last_name']
        if 'email' in data:
            user.email = data['email']
        if 'phone' in data or 'phone_number' in data:
            user.phone_number = data.get('phone') or data.get('phone_number')
        
        # Update location
        if 'city' in data:
            user.city = data['city']
        if 'state' in data:
            user.state = data['state']
        if 'pincode' in data:
            user.pincode = data['pincode']
        
        # Update donor-specific fields
        if 'blood_group' in data:
            user.blood_group = data['blood_group']
        if 'last_donation_date' in data and data['last_donation_date']:
            user.last_donation_date = data['last_donation_date']
        if 'is_available' in data:
            user.is_available = data['is_available']
        
        # Update UI preferences
        if 'theme' in data:
            user.theme = data['theme']
        
        user.save()
        
        # Update Notification Settings if provided
        if hasattr(user, 'notification_settings'):
            notif_settings = user.notification_settings
            notif_fields = [
                'blood_request_alerts', 'emergency_alerts', 'nearby_donation_requests',
                'donation_reminders', 'chat_notifications', 'system_updates',
                'email_notifications', 'sms_notifications', 'push_notifications',
                'quiet_hours_enabled', 'search_radius_km'
            ]
            
            for field in notif_fields:
                if field in data:
                    setattr(notif_settings, field, data[field])
            
            if 'quiet_hours_start' in data:
                notif_settings.quiet_hours_start = data['quiet_hours_start']
            if 'quiet_hours_end' in data:
                notif_settings.quiet_hours_end = data['quiet_hours_end']
            
            notif_settings.save()
        
        # Update Privacy Settings if provided
        if hasattr(user, 'privacy_settings'):
            privacy_settings = user.privacy_settings
            privacy_fields = [
                'profile_visibility', 'show_phone_number', 'show_email',
                'show_last_donation_date', 'show_location', 'anonymous_mode',
                'location_sharing_enabled', 'live_location_during_emergency',
                'enable_chat_requests'
            ]
            
            for field in privacy_fields:
                if field in data:
                    setattr(privacy_settings, field, data[field])
            
            privacy_settings.save()
        
        # Update Donor Profile if provided
        if hasattr(user, 'donor_profile'):
            donor_profile = user.donor_profile
            donor_fields = [
                'availability_status', 'total_donations', 'weight_kg',
                'has_recent_illness', 'medical_restrictions',
                'emergency_contact_name', 'emergency_contact_phone',
                'emergency_contact_relation', 'donation_frequency_preference'
            ]
            
            for field in donor_fields:
                if field in data:
                    setattr(donor_profile, field, data[field])
            
            # Auto-calculate next eligible date if last donation updated
            if 'last_donation_date' in data:
                donor_profile.calculate_next_eligible_date()
            
            donor_profile.save()
        
        return Response({
            'success': True,
            'message': 'Settings updated successfully'
        }, status=status.HTTP_200_OK)
        
    except Exception as e:
        logger.error(f'Error updating settings: {str(e)}')
        return Response({
            'success': False,
            'message': f'Failed to update settings: {str(e)}'
        }, status=status.HTTP_400_BAD_REQUEST)


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def change_password(request):
    """API endpoint to change password"""
    try:
        user = request.user
        data = request.data

        current_password = data.get('current_password')
        new_password = data.get('new_password')
        confirm_password = data.get('confirm_password')

        # Validate inputs
        if not current_password or not new_password or not confirm_password:
            return Response({
                'success': False,
                'message': 'All fields are required'
            }, status=status.HTTP_400_BAD_REQUEST)

        if new_password != confirm_password:
            return Response({
                'success': False,
                'message': 'New passwords do not match'
            }, status=status.HTTP_400_BAD_REQUEST)

        if len(new_password) < 8:
            return Response({
                'success': False,
                'message': 'Password must be at least 8 characters long'
            }, status=status.HTTP_400_BAD_REQUEST)

        # Verify current password
        if not user.check_password(current_password):
            return Response({
                'success': False,
                'message': 'Current password is incorrect'
            }, status=status.HTTP_400_BAD_REQUEST)

        # Set new password
        user.set_password(new_password)
        user.save()

        return Response({
            'success': True,
            'message': 'Password changed successfully'
        }, status=status.HTTP_200_OK)

    except Exception as e:
        logger.error(f'Error changing password: {str(e)}')
        return Response({
            'success': False,
            'message': f'Failed to change password: {str(e)}'
        }, status=status.HTTP_400_BAD_REQUEST)


@login_required
def edit_profile(request):
    """
    Profile editing page - allows photo upload and location update
    Phase 2 Feature
    """
    try:
        # Get or create donor profile
        donor_profile, created = DonorProfile.objects.get_or_create(
            user=request.user
        )

        if request.method == 'POST':
            # Handle profile photo upload
            if 'profile_photo' in request.FILES:
                profile_photo = request.FILES['profile_photo']
                # Validate file size (max 5MB)
                if profile_photo.size > 5 * 1024 * 1024:
                    messages.error(request, 'Photo must be less than 5MB')
                    return redirect('edit_profile')

                # Validate file type
                allowed_types = ['image/jpeg', 'image/png', 'image/jpg']
                if profile_photo.content_type not in allowed_types:
                    messages.error(request, 'Only JPEG and PNG images are allowed')
                    return redirect('edit_profile')

                # Delete old photo if exists
                if donor_profile.profile_photo:
                    if default_storage.exists(donor_profile.profile_photo.name):
                        default_storage.delete(donor_profile.profile_photo.name)

                # Save new photo
                donor_profile.profile_photo = profile_photo
                donor_profile.save()
                messages.success(request, 'Profile photo updated successfully')

            # Handle location update
            if 'city' in request.POST or 'state' in request.POST:
                if request.POST.get('city'):
                    request.user.city = request.POST['city']
                if request.POST.get('state'):
                    request.user.state = request.POST['state']
                if request.POST.get('pincode'):
                    request.user.pincode = request.POST['pincode']
                request.user.save()
                messages.success(request, 'Location updated successfully')

            return redirect('edit_profile')

        context = {
            'user': request.user,
            'donor_profile': donor_profile,
        }
        return render(request, 'accounts/edit_profile.html', context)

    except Exception as e:
        logger.error(f'Error in edit_profile: {str(e)}', exc_info=True)
        messages.error(request, 'An error occurred while updating your profile')
        return redirect('edit_profile')


@login_required
@require_POST
def remove_profile_photo(request):
    """
    Remove profile photo - AJAX endpoint
    Phase 2 Feature
    """
    try:
        donor_profile = request.user.donor_profile

        if donor_profile.profile_photo:
            if default_storage.exists(donor_profile.profile_photo.name):
                default_storage.delete(donor_profile.profile_photo.name)
            donor_profile.profile_photo = None
            donor_profile.save()

        return JsonResponse({
            'success': True,
            'message': 'Profile photo removed successfully'
        })

    except Exception as e:
        logger.error(f'Error removing profile photo: {str(e)}', exc_info=True)
        return JsonResponse({
            'success': False,
            'message': 'Failed to remove profile photo'
        }, status=400)


@login_required
def toggle_favorite_donor(request, donor_id):
    """
    Toggle donor as favorite - AJAX endpoint
    Phase 2 Feature
    """
    try:
        favorite_donor = get_object_or_404(User, id=donor_id, user_type='donor')

        # Prevent users from favoriting themselves
        if favorite_donor == request.user:
            return JsonResponse({
                'success': False,
                'message': 'You cannot favorite yourself'
            }, status=400)

        # Check if already favorited
        favorite = FavoriteDonor.objects.filter(
            user=request.user,
            favorite_donor=favorite_donor
        ).first()

        if favorite:
            # Remove from favorites
            favorite.delete()
            return JsonResponse({
                'success': True,
                'is_favorite': False,
                'message': 'Removed from favorites'
            })
        else:
            # Add to favorites
            FavoriteDonor.objects.create(
                user=request.user,
                favorite_donor=favorite_donor
            )
            return JsonResponse({
                'success': True,
                'is_favorite': True,
                'message': 'Added to favorites'
            })

    except Exception as e:
        logger.error(f'Error toggling favorite donor: {str(e)}', exc_info=True)
        return JsonResponse({
            'success': False,
            'message': 'Failed to toggle favorite'
        }, status=400)


@login_required
def favorites_list(request):
    """
    Display list of favorite donors
    Phase 2 Feature
    """
    try:
        favorites = FavoriteDonor.objects.filter(
            user=request.user
        ).select_related('favorite_donor')

        context = {
            'favorites': favorites,
        }
        return render(request, 'accounts/favorites.html', context)

    except Exception as e:
        logger.error(f'Error loading favorites: {str(e)}', exc_info=True)
        return render(request, 'accounts/favorites.html', {'error': 'Failed to load favorites'})


# ============================================================================
# PUBLIC PROFILE & FOLLOW SYSTEM (Instagram-style)
# ============================================================================

def public_profile_view(request, user_id):
    """View another user's public profile with follow/unfollow functionality"""
    profile_user = get_object_or_404(User, id=user_id, is_active=True)
    
    # Check if viewing own profile
    is_own_profile = request.user.is_authenticated and request.user == profile_user
    
    # Get privacy settings
    privacy_settings = getattr(profile_user, 'privacy_settings', None)
    
    # Check if profile is private and user is not following
    is_private = False
    is_following = False
    
    if request.user.is_authenticated and not is_own_profile:
        # Check if current user follows this user
        is_following = Follow.objects.filter(
            follower=request.user, 
            following=profile_user
        ).exists()
        
        # Check if profile is private
        if privacy_settings and privacy_settings.profile_visibility == 'private':
            if not is_following and not request.user.is_staff:
                is_private = True
    
    # Get user's blood requests (only if not private or is follower/owner)
    user_requests = []
    if not is_private or is_following or is_own_profile or (request.user.is_authenticated and request.user.is_staff):
        try:
            from blood_requests_app.models import BloodRequest
            user_requests = BloodRequest.objects.filter(
                requester=profile_user
            ).order_by('-created_at')[:10]
        except Exception as e:
            logger.error(f'Error fetching user requests: {str(e)}')
    
    # Get follower/following counts
    followers_count = Follow.objects.filter(following=profile_user).count()
    following_count = Follow.objects.filter(follower=profile_user).count()
    
    # Check if anonymous mode is enabled
    anonymous_mode = False
    if privacy_settings:
        anonymous_mode = privacy_settings.anonymous_mode
    
    context = {
        'profile_user': profile_user,
        'user_requests': user_requests,
        'is_following': is_following,
        'is_own_profile': is_own_profile,
        'is_private': is_private,
        'followers_count': followers_count,
        'following_count': following_count,
        'anonymous_mode': anonymous_mode,
        'privacy_settings': privacy_settings,
    }
    
    return render(request, 'accounts/public_profile.html', context)


@login_required
def toggle_follow(request, user_id):
    """Toggle follow/unfollow user (AJAX endpoint)"""
    try:
        user_to_follow = get_object_or_404(User, id=user_id, is_active=True)
        
        # Prevent users from following themselves
        if user_to_follow == request.user:
            return JsonResponse({
                'success': False,
                'error': 'You cannot follow yourself'
            }, status=400)
        
        # Check if already following
        follow, created = Follow.objects.get_or_create(
            follower=request.user,
            following=user_to_follow
        )
        
        if not created:
            # Already following, so unfollow
            follow.delete()
            
            # Get updated counts
            followers_count = Follow.objects.filter(following=user_to_follow).count()
            
            return JsonResponse({
                'success': True,
                'is_following': False,
                'followers_count': followers_count,
                'message': f'Unfollowed {user_to_follow.first_name or user_to_follow.username}'
            })
        else:
            # Now following
            # Get updated counts
            followers_count = Follow.objects.filter(following=user_to_follow).count()
            
            # Create notification for the followed user
            try:
                from notifications.models import Notification
                Notification.objects.create(
                    user=user_to_follow,
                    notification_type='general',
                    title='New Follower',
                    message=f'{request.user.first_name or request.user.username} started following you',
                    priority='low'
                )
            except Exception as e:
                logger.error(f'Error creating follow notification: {str(e)}')
            
            return JsonResponse({
                'success': True,
                'is_following': True,
                'followers_count': followers_count,
                'message': f'Now following {user_to_follow.first_name or user_to_follow.username}'
            })
            
    except Exception as e:
        logger.error(f'Error toggling follow: {str(e)}', exc_info=True)
        return JsonResponse({
            'success': False,
            'error': 'Failed to toggle follow status'
        }, status=500)


@login_required
def followers_list(request, user_id):
    """Show list of followers for a user"""
    user = get_object_or_404(User, id=user_id, is_active=True)
    
    # Check privacy settings
    privacy_settings = getattr(user, 'privacy_settings', None)
    is_private = privacy_settings and privacy_settings.profile_visibility == 'private'
    
    # Check if current user can view followers
    can_view = (
        request.user == user or  # Own profile
        request.user.is_staff or  # Admin
        not is_private or  # Public profile
        Follow.objects.filter(follower=request.user, following=user).exists()  # Is following
    )
    
    if not can_view:
        messages.error(request, 'This profile is private')
        return redirect('public-profile', user_id=user_id)
    
    followers = Follow.objects.filter(following=user).select_related('follower')
    
    context = {
        'profile_user': user,
        'followers': followers,
        'is_own_profile': request.user == user,
    }
    
    return render(request, 'accounts/followers_list.html', context)


@login_required
def following_list(request, user_id):
    """Show list of users that a user is following"""
    user = get_object_or_404(User, id=user_id, is_active=True)
    
    # Check privacy settings
    privacy_settings = getattr(user, 'privacy_settings', None)
    is_private = privacy_settings and privacy_settings.profile_visibility == 'private'
    
    # Check if current user can view following
    can_view = (
        request.user == user or  # Own profile
        request.user.is_staff or  # Admin
        not is_private or  # Public profile
        Follow.objects.filter(follower=request.user, following=user).exists()  # Is following
    )
    
    if not can_view:
        messages.error(request, 'This profile is private')
        return redirect('public-profile', user_id=user_id)
    
    following = Follow.objects.filter(follower=user).select_related('following')
    
    context = {
        'profile_user': user,
        'following': following,
        'is_own_profile': request.user == user,
    }
    
    return render(request, 'accounts/following_list.html', context)
