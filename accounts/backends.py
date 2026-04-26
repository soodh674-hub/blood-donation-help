"""
Custom Email Backend for Brevo (Sendinblue) HTTP API
Uses API key instead of SMTP authentication
"""
import logging
import requests
from django.core.mail.backends.base import BaseEmailBackend
from django.conf import settings

logger = logging.getLogger(__name__)


class BrevoEmailBackend(BaseEmailBackend):
    """
    Email backend that sends emails via Brevo HTTP API
    """
    
    def __init__(self, fail_silently=False, **kwargs):
        super().__init__(fail_silently=fail_silently, **kwargs)
        self.api_key = getattr(settings, 'BREVO_API_KEY', '')
        self.api_url = 'https://api.brevo.com/v3/smtp/email'
        
        if not self.api_key:
            logger.error("BREVO_API_KEY not configured in settings")
    
    def send_messages(self, email_messages):
        """
        Send a list of email messages via Brevo HTTP API
        """
        if not self.api_key:
            if not self.fail_silently:
                raise ValueError("BREVO_API_KEY not configured")
            return 0
        
        sent_count = 0
        headers = {
            'accept': 'application/json',
            'api-key': self.api_key,
            'content-type': 'application/json',
        }
        
        for message in email_messages:
            try:
                # Prepare email data for Brevo API
                email_data = {
                    'sender': {
                        'name': 'BloodLife',
                        'email': message.from_email
                    },
                    'to': [{'email': addr for addr in message.to}],
                    'subject': message.subject,
                    'htmlContent': message.html_body if message.html_body else message.body,
                    'textContent': message.body,
                }
                
                # Add CC if present
                if message.cc:
                    email_data['cc'] = [{'email': addr} for addr in message.cc]
                
                # Add BCC if present
                if message.bcc:
                    email_data['bcc'] = [{'email': addr} for addr in message.bcc]
                
                # Send via Brevo API
                response = requests.post(
                    self.api_url,
                    json=email_data,
                    headers=headers,
                    timeout=30
                )
                
                if response.status_code in [200, 201, 202]:
                    sent_count += 1
                    logger.info(f"Email sent successfully to {message.to}")
                else:
                    logger.error(f"Failed to send email to {message.to}: {response.status_code} - {response.text}")
                    if not self.fail_silently:
                        raise Exception(f"Brevo API error: {response.status_code} - {response.text}")
                        
            except Exception as e:
                logger.error(f"Error sending email to {message.to}: {str(e)}")
                if not self.fail_silently:
                    raise
        
        return sent_count
