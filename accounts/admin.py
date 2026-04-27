from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from django.contrib import messages
from django.db import transaction
from django.db.utils import ProgrammingError
from .models import User, UserReport, DonorRating, FavoriteDonor, Follow, PasswordResetOTP, LoginOTP, UserActivityLog
import logging

logger = logging.getLogger(__name__)

@admin.register(User)
class UserAdmin(BaseUserAdmin):
    list_display = ['username', 'email', 'user_type', 'blood_group', 'city', 'is_verified', 'is_eligible_donor']
    list_filter = ['user_type', 'blood_group', 'is_verified', 'is_available', 'created_at']
    search_fields = ['username', 'email', 'first_name', 'last_name', 'city']
    readonly_fields = ['created_at', 'updated_at', 'days_since_last_donation']
    
    fieldsets = BaseUserAdmin.fieldsets + (
        ('Blood Donation Info', {
            'fields': (
                'user_type', 'phone_number', 'blood_group', 'date_of_birth',
                'last_donation_date', 'days_since_last_donation', 'is_verified',
                'is_available', 'privacy_level'
            )
        }),
        ('Location', {
            'fields': ('city', 'state', 'country', 'pincode', 'latitude', 'longitude')
        }),
        ('Medical Info', {
            'fields': ('has_medical_conditions', 'medical_conditions', 'last_medical_checkup')
        }),
        ('GDPR Compliance', {
            'fields': ('consent_given', 'data_retention_consent', 'created_at', 'updated_at')
        }),
    )
    
    add_fieldsets = BaseUserAdmin.add_fieldsets + (
        ('Blood Donation Info', {
            'fields': (
                'user_type', 'phone_number', 'blood_group', 'date_of_birth',
                'is_verified', 'privacy_level'
            )
        }),
    )
    
    def delete_model(self, request, obj):
        """Override delete_model to handle cascade delete errors"""
        try:
            with transaction.atomic():
                # Manually delete related objects that might cause issues
                self._delete_related_objects(obj)
                # Now delete the user
                obj.delete()
                messages.success(request, f'User "{obj.username}" was deleted successfully.')
        except ProgrammingError as e:
            # Handle missing database columns (migration not applied)
            error_msg = str(e)
            if 'verified_by_id' in error_msg or 'does not exist' in error_msg:
                logger.warning(f'Database migration not applied: {error_msg}')
                messages.error(
                    request, 
                    'Database migration required. Please run: python manage.py migrate'
                )
            else:
                logger.error(f'Error deleting user {obj.username}: {str(e)}', exc_info=True)
                messages.error(request, f'Error deleting user: {str(e)}')
        except Exception as e:
            logger.error(f'Error deleting user {obj.username}: {str(e)}', exc_info=True)
            messages.error(request, f'Error deleting user: {str(e)}. Some related data may not exist in the database.')
    
    def delete_queryset(self, request, queryset):
        """Override delete_queryset to handle cascade delete errors for bulk delete"""
        try:
            with transaction.atomic():
                for obj in queryset:
                    try:
                        # Manually delete related objects
                        self._delete_related_objects(obj)
                        # Delete the user
                        obj.delete()
                    except ProgrammingError as e:
                        # Handle missing database columns
                        error_msg = str(e)
                        if 'verified_by_id' in error_msg or 'does not exist' in error_msg:
                            logger.warning(f'Database migration not applied: {error_msg}')
                            messages.warning(
                                request, 
                                f'Could not delete user "{obj.username}": Database migration required. Run: python manage.py migrate'
                            )
                        else:
                            logger.error(f'Error deleting user {obj.username}: {str(e)}', exc_info=True)
                            messages.warning(request, f'Could not delete user "{obj.username}": {str(e)}')
                    except Exception as e:
                        logger.error(f'Error deleting user {obj.username}: {str(e)}', exc_info=True)
                        messages.warning(request, f'Could not delete user "{obj.username}": {str(e)}')
                messages.success(request, 'Bulk delete completed with some warnings.')
        except ProgrammingError as e:
            error_msg = str(e)
            if 'verified_by_id' in error_msg or 'does not exist' in error_msg:
                logger.warning(f'Database migration not applied in bulk delete: {error_msg}')
                messages.error(
                    request, 
                    'Database migration required. Please run: python manage.py migrate'
                )
            else:
                logger.error(f'Error in bulk delete: {str(e)}', exc_info=True)
                messages.error(request, f'Error in bulk delete: {str(e)}')
        except Exception as e:
            logger.error(f'Error in bulk delete: {str(e)}', exc_info=True)
            messages.error(request, f'Error in bulk delete: {str(e)}')
    
    def _delete_related_objects(self, user):
        """Helper method to delete related objects safely"""
        # Try to delete each related model individually
        related_models = [
            ('UserReport', UserReport),
            ('DonorRating', DonorRating),
            ('FavoriteDonor', FavoriteDonor),
            ('Follow', Follow),
            ('PasswordResetOTP', PasswordResetOTP),
            ('LoginOTP', LoginOTP),
            ('UserActivityLog', UserActivityLog),
        ]
        
        for model_name, model_class in related_models:
            try:
                # Try to find and delete related objects
                if model_name == 'UserReport':
                    model_class.objects.filter(reporter=user).delete()
                    model_class.objects.filter(reported_user=user).delete()
                elif model_name == 'DonorRating':
                    model_class.objects.filter(donor=user).delete()
                    model_class.objects.filter(rater=user).delete()
                elif model_name == 'FavoriteDonor':
                    model_class.objects.filter(user=user).delete()
                    model_class.objects.filter(favorite_donor=user).delete()
                elif model_name == 'Follow':
                    model_class.objects.filter(follower=user).delete()
                    model_class.objects.filter(following=user).delete()
                elif model_name == 'PasswordResetOTP':
                    model_class.objects.filter(user=user).delete()
                elif model_name == 'LoginOTP':
                    model_class.objects.filter(user=user).delete()
                elif model_name == 'UserActivityLog':
                    model_class.objects.filter(user=user).delete()
            except Exception as e:
                # Log but don't fail if a related model doesn't exist
                logger.warning(f'Could not delete {model_name} for user {user.username}: {str(e)}')