from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from django.contrib import messages
from .models import User
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
            obj.delete()
            messages.success(request, f'User "{obj.username}" was deleted successfully.')
        except Exception as e:
            logger.error(f'Error deleting user {obj.username}: {str(e)}', exc_info=True)
            messages.error(request, f'Error deleting user: {str(e)}. Some related data may not exist in the database.')
    
    def delete_queryset(self, request, queryset):
        """Override delete_queryset to handle cascade delete errors for bulk delete"""
        try:
            for obj in queryset:
                try:
                    obj.delete()
                except Exception as e:
                    logger.error(f'Error deleting user {obj.username}: {str(e)}', exc_info=True)
                    messages.warning(request, f'Could not delete user "{obj.username}": {str(e)}')
            messages.success(request, 'Bulk delete completed with some warnings.')
        except Exception as e:
            logger.error(f'Error in bulk delete: {str(e)}', exc_info=True)
            messages.error(request, f'Error in bulk delete: {str(e)}')