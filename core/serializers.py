from rest_framework import serializers
from django.contrib.auth import get_user_model
from .models import BloodBank, BloodInventory, DonationRequest, Donation

User = get_user_model()

class UserSerializer(serializers.ModelSerializer):
    password = serializers.CharField(write_only=True, required=True, min_length=6)
    class Meta:
        model = User
        fields = ('id','username','email','password','first_name','last_name','role','phone','city','blood_group','profile_photo')
    def create(self, validated_data):
        password = validated_data.pop('password')
        user = User(**validated_data)
        user.set_password(password)
        user.save()
        return user

class BloodBankSerializer(serializers.ModelSerializer):
    class Meta:
        model = BloodBank
        fields = '__all__'

class BloodInventorySerializer(serializers.ModelSerializer):
    class Meta:
        model = BloodInventory
        fields = '__all__'

class DonationRequestSerializer(serializers.ModelSerializer):
    requester = UserSerializer(read_only=True)
    class Meta:
        model = DonationRequest
        fields = '__all__'
        read_only_fields = ('status','created_at','approved_by')
    def validate_units(self, value):
        if value <= 0:
            raise serializers.ValidationError('Units must be > 0')
        return value
    def validate(self, data):
        user = self.context['request'].user
        if DonationRequest.objects.filter(requester=user, status='pending').exists():
            raise serializers.ValidationError('You already have a pending request.')
        return data

class DonationSerializer(serializers.ModelSerializer):
    donor = UserSerializer(read_only=True)
    class Meta:
        model = Donation
        fields = '__all__'
        read_only_fields = ('approved','approved_by','date')
