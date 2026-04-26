from django.test import Client, TestCase, override_settings

from accounts.models import User


@override_settings(ALLOWED_HOSTS=['testserver', 'localhost', '127.0.0.1'])
class DonorViewsTests(TestCase):
    def setUp(self):
        self.client = Client()
        self.donor = User.objects.create_user(
            username='donor_a',
            password='testpass123',
            user_type='donor',
            blood_group='A+',
            first_name='Donor',
            last_name='One',
            city='Delhi',
            state='Delhi',
            is_available=True,
            is_active=True,
        )
        self.viewer = User.objects.create_user(
            username='viewer',
            password='testpass123',
            user_type='hospital',
        )

    def test_public_donor_search_returns_results(self):
        response = self.client.get('/api/donors/search/', {'blood_group': 'A+'})

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json()['count'], 1)
        self.assertIn('profile_photo', response.json()['results'][0]['donor'])

    def test_donor_profile_page_loads(self):
        self.client.force_login(self.viewer)

        response = self.client.get(f'/donors/profile/{self.donor.id}/')

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, self.donor.username)
