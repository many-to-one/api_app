from rest_framework import serializers
from ..models import Secret, Address

class SecretSerializer(serializers.ModelSerializer):
    # account_name = serializers.CharField(source='account.name')

    class Meta:
        model = Secret
        fields = '__all__'

class AddressSerializer(serializers.ModelSerializer):
    # name = serializers.CharField(source='name.name')

    class Meta:
        model = Address
        fields = '__all__'
