# myapp/authentication.py

from rest_framework.authentication import BaseAuthentication
from rest_framework.exceptions import AuthenticationFailed
import requests


class CustomAuthentication(BaseAuthentication):
    def authenticate(self, request):
        authorization_header = request.headers.get('Authorization')

        if not authorization_header:
            return None

        id_token = authorization_header.split(" ")[1]

        response = requests.get(
            'https://www.googleapis.com/oauth2/v3/tokeninfo',
            params={'id_token': id_token}
        )

        if response.status_code != 200:
            raise AuthenticationFailed('Invalid ID token')

        user_info = response.json()
        google_id = user_info['sub']
        email = user_info['email']
        name = user_info['name']

        # Retrieve or create the customer
        from .models import Customer
        customer, created = Customer.objects.update_or_create(
            google_id=google_id,
            defaults={'email': email, 'name': name}
        )

        return customer, None
