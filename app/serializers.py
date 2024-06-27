from rest_framework import serializers
from app.models import Customer, Order


class CustomerSerializer(serializers.ModelSerializer):
    class Meta:
        model = Customer
        fields = '__all__'


class OrderSerializer(serializers.ModelSerializer):
    class Meta:
        model = Order
        fields = '__all__'


class CreateOrderSerializer(serializers.Serializer):
    phone_number = serializers.CharField(required=True)
    item = serializers.CharField(required=True)
    amount = serializers.IntegerField(required=True)
