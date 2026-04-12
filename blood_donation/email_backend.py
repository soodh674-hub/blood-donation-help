import requests
import logging
from django.conf import settings
from django.core.mail.backends.base import BaseEmailBackend
from django.core.mail import EmailMessage

logger = logging.getLogger(__name__)


class BrevoAPIEmailBackend(BaseEmailBackend):
    """
    Email backend that uses Brevo HTTP API instead of SMTP.
    This is more reliable on Render free tier as it avoids SMTP port blocking.
    
    Uses pure HTTP requests instead of Brevo SDK for better compatibility.
    """
    
    # Brevo API endpoint
    API_URL = "https://api.brevo.com/v3/smtp/email"
    
    def __init__(self, api_key=None, fail_silently=False, **kwargs):
        super().__init__(fail_silently=fail_silently, **kwargs)
        
        # Get API key from settings if not provided
        if api_key is None:
            api_key = getattr(settings, 'BREVO_API_KEY', '')
        
        # Strip any whitespace/newlines from the API key
        self.api_key = api_key.strip() if api_key else ''
        
        # Log configuration on initialization
        if not self.api_key:
            logger.warning("BREVO_API_KEY is not configured. Email sending will fail!")
        else:
            logger.info(f"Brevo API backend initialized (key length: {len(self.api_key)})")
    
    def send_messages(self, messages):
        """
        Send email messages using Brevo HTTP API.
        """
        if not self.api_key:
            logger.error("Cannot send emails: BREVO_API_KEY is not configured")
            if not self.fail_silently:
                raise Exception("BREVO_API_KEY is not configured")
            return 0
        
        num_sent = 0
        for message in messages:
            try:
                result = self._send_brevo_email(message)
                if result:
                    num_sent += 1
            except Exception as e:
                logger.error(f"Error sending email via Brevo API: {str(e)}")
                if not self.fail_silently:
                    raise
        
        return num_sent
    
    def _send_brevo_email(self, email_message):
        """
        Send a single email using Brevo HTTP API.
        """
        # Prepare headers
        headers = {
            "accept": "application/json",
            "api-key": self.api_key,
            "content-type": "application/json"
        }
        
        # Prepare sender info
        sender_name = getattr(settings, 'DEFAULT_FROM_EMAIL_NAME', 'Project Admin')
        sender_email = getattr(settings, 'DEFAULT_FROM_EMAIL', 'noreply@yourdomain.com')
        
        # Build payload
        payload = {
            "sender": {
                "name": sender_name,
                "email": sender_email
            },
            "to": [
                {"email": to_addr} for to_addr in email_message.to
            ],
            "subject": email_message.subject,
        }
        
        # Add HTML content if available, otherwise plain text
        if hasattr(email_message, 'alternatives') and email_message.alternatives:
            # Check if there's HTML alternative
            for alternative in email_message.alternatives:
                if alternative[1] == 'text/html':
                    payload["htmlContent"] = alternative[0]
                    break
        
        # If no HTML content, use plain text
        if "htmlContent" not in payload:
            payload["htmlContent"] = email_message.body.replace('\n', '<br>')
        
        # Make API request
        try:
            response = requests.post(
                self.API_URL,
                json=payload,
                headers=headers,
                timeout=15  # 15 second timeout
            )
            
            # Log response
            logger.info(f"Brevo API response status: {response.status_code}")
            logger.info(f"Brevo API response body: {response.text}")
            
            # Parse response to check if actually queued
            if response.status_code == 201:
                try:
                    response_data = response.json()
                    logger.info(f"Brevo response data: {response_data}")
                    if 'messageId' in response_data or 'id' in response_data:
                        message_id = response_data.get('messageId', response_data.get('id'))
                        logger.info(f"✅ Email QUEUED with message ID: {message_id}")
                    else:
                        logger.warning(f"⚠️ Brevo accepted email but no message ID returned: {response_data}")
                except Exception as parse_error:
                    logger.error(f"Failed to parse Brevo response: {parse_error}")
            
            # Check if successful
            if response.status_code in [200, 201]:
                logger.info(f"Email sent successfully via Brevo API to {email_message.to}")
                return True
            else:
                logger.error(f"Brevo API error: {response.status_code} - {response.text}")
                if not self.fail_silently:
                    raise Exception(f"Brevo API error: {response.status_code}")
                return False
                
        except requests.exceptions.Timeout as e:
            logger.error(f"Brevo API request timed out: {str(e)}")
            if not self.fail_silently:
                raise
            return False
        except requests.exceptions.RequestException as e:
            logger.error(f"Brevo API request failed: {str(e)}")
            if not self.fail_silently:
                raise
            return False
