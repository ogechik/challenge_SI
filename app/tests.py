from unittest.mock import patch

from django.conf import settings
from django.test import TestCase
from rest_framework import status
from rest_framework.reverse import reverse
from django.utils.http import urlencode
from rest_framework.test import APITestCase, APIClient

from app.models import Customer, Order


class CustomerModelTestCase(TestCase):
    def create_customer(self):
        return Customer.objects.create(
            google_id='982492387498234',
            name='John Doe',
            email='j@test.com',
        )

    def test_customer_creation(self):
        customer = self.create_customer()
        self.assertTrue(isinstance(customer, Customer))
        self.assertEqual(customer.__str__(), f'{customer.name} - {customer.email}')


class GoogleLoginViewTest(TestCase):
    def test_google_login_redirection(self):
        response = self.client.get(reverse('login'))
        self.assertEqual(response.status_code, 302)
        google_auth_base_url = "https://accounts.google.com/o/oauth2/auth"
        params = {
            "response_type": "code",
            "client_id": settings.GOOGLE_CLIENT_ID,
            "redirect_uri": settings.GOOGLE_REDIRECT_URI,
            "scope": "openid email profile",
            "access_type": "offline",
            "prompt": "consent"
        }
        auth_url = f"{google_auth_base_url}?{urlencode(params)}"

        self.assertEqual(response['Location'], auth_url)


class GoogleCallbackViewTest(TestCase):
    @patch('requests.post')
    @patch('requests.get')
    def test_google_callback(self, mock_get, mock_post):
        mock_post.return_value.json.return_value = {
            'access_token': 'mock_access_token',
            'id_token': 'mock_id_token'
        }
        mock_get.return_value.json.return_value = {
            'sub': 'mock_google_id',
            'email': 'test@test.com',
            'name': 'Test User'
        }
        response = self.client.get(reverse('auth2callback'), {'code': 'mock_code'})

        self.assertEqual(response.status_code, 200)
        customer = Customer.objects.get(google_id='mock_google_id')
        self.assertEqual(customer.email, 'test@test.com')
        self.assertEqual(customer.name, 'Test User')


class OrderViewSetTest(APITestCase):
    def setUp(self):
        self.client = APIClient()

        self.customer = Customer.objects.create(
            id=1,
            name='Test User',
            email='test@example.com',
            phone_number='+254712345678'
        )

        self.user = self.customer

        self.client.force_authenticate(user=self.user)

        self.valid_payload = {
            'item': 'Test Item',
            'amount': 100,
            'phone_number': '+254712345678'
        }

        self.invalid_payload = {
            'item': '',
            'amount': '',
            'phone_number': ''
        }

    @patch('app.utils.send_order_creation_sms')
    def test_create_order_valid_payload(self, mock_send_sms):
        mock_send_sms.return_value = "SMS sent"
        response = self.client.post(reverse('order-list'), self.valid_payload)  # assuming 'order-list' is the URL name
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(Order.objects.count(), 1)
        self.assertEqual(Order.objects.get().item, 'Test Item')

    def test_create_order_invalid_payload(self):
        response = self.client.post(reverse('order-list'), self.invalid_payload)

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
