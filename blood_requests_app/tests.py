from unittest.mock import patch

from django.test import TestCase, override_settings
from rest_framework.test import APIClient

from blood_requests_app.models_chat import ChatbotConversation


@override_settings(ALLOWED_HOSTS=['testserver', 'localhost', '127.0.0.1'])
class ChatbotViewTests(TestCase):
    def setUp(self):
        self.client = APIClient()

    @patch('blood_requests_app.chatbot_service.get_chatbot_response')
    def test_chatbot_reuses_existing_session_id(self, mock_get_chatbot_response):
        mock_get_chatbot_response.return_value = {
            'response': 'Mock chatbot reply',
            'confidence': 'high',
            'suggestions': ['next step'],
            'context': {'topic': 'donation'},
        }

        first_response = self.client.post(
            '/api/requests/chatbot/',
            {'message': 'hello', 'session_id': 'fixed-session'},
            format='json',
        )
        second_response = self.client.post(
            '/api/requests/chatbot/',
            {'message': 'hello again', 'session_id': 'fixed-session'},
            format='json',
        )

        self.assertEqual(first_response.status_code, 200)
        self.assertEqual(second_response.status_code, 200)
        self.assertEqual(ChatbotConversation.objects.count(), 1)
        self.assertEqual(
            ChatbotConversation.objects.get(session_id='fixed-session').user_message,
            'hello again',
        )
