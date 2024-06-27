from django.shortcuts import redirect
from django.conf import settings
from django.utils.http import urlencode
from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import AllowAny, IsAuthenticated

from app.at_client import sms
from app.permission import HasPermission
from app.serializers import CustomerSerializer, OrderSerializer, CreateOrderSerializer
import requests

from app.models import Customer, Order
from app.utils import send_order_creation_sms


class GoogleLoginView(APIView):
    permission_classes = [AllowAny]

    def get(self, request):
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

        return redirect(auth_url)


class GoogleCallbackView(APIView):
    permission_classes = [AllowAny]

    def get(self, request):
        code = request.GET.get('code')
        token_url = "https://oauth2.googleapis.com/token"
        token_data = {
            "code": code,
            "client_id": settings.GOOGLE_CLIENT_ID,
            "client_secret": settings.GOOGLE_CLIENT_SECRET,
            "redirect_uri": settings.GOOGLE_REDIRECT_URI,
            "grant_type": "authorization_code"
        }
        token_response = requests.post(token_url, data=token_data).json()
        access_token = token_response.get('access_token')
        id_token = token_response.get('id_token')

        user_info_url = "https://www.googleapis.com/oauth2/v3/userinfo"
        user_info_response = requests.get(user_info_url, headers={"Authorization": f"Bearer {access_token}"}).json()

        google_id = user_info_response['sub']
        email = user_info_response['email']
        name = user_info_response['name']

        from app.models import Customer
        customer, created = Customer.objects.update_or_create(
            google_id=google_id,
            defaults={'email': email, 'name': name}
        )

        return Response({
            'id': customer.id,
            'name': customer.name,
            'email': customer.email,
            'access_token': access_token,
            'id_token': id_token
        })


class CustomerViewSet(viewsets.ModelViewSet):
    queryset = Customer.objects.all()
    serializer_class = CustomerSerializer
    permission_classes = [HasPermission]


class OrderViewSet(viewsets.ModelViewSet):
    queryset = Order.objects.all()
    serializer_class = OrderSerializer
    permission_classes = [HasPermission]

    def create(self, request, *args, **kwargs):
        serializer = CreateOrderSerializer(data=request.data)
        if serializer.is_valid():
            try:
                item = serializer.validated_data['item']
                amount = serializer.validated_data['amount']
                phone_number = serializer.validated_data['phone_number']

                # get customer
                customer = Customer.objects.get(pk=request.user.id)

                # create new order
                new_order = Order.objects.create(
                    customer_id=request.user.id,
                    item=item,
                    amount=amount,
                )

                # update customer phone number
                customer.phone_number = phone_number
                customer.save()

                # send message to customer's phone number.
                response = send_order_creation_sms(new_order.id, customer.name, phone_number)
                # print(response)

                order = self.serializer_class(new_order)
                return Response(order.data, status=status.HTTP_201_CREATED)
            except Customer.DoesNotExist:
                return Response({'error': 'customer not found'}, status=status.HTTP_404_NOT_FOUND)
            except Exception as e:
                return Response({'error': 'Error creating new order.'}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
