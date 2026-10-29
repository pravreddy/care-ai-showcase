"""
Auth Serializers - SignSimple UK
"""
from rest_framework import serializers
from django.contrib.auth import authenticate
from .models import User


class RegisterSerializer(serializers.ModelSerializer):
    password = serializers.CharField(write_only=True, min_length=8)
    password2 = serializers.CharField(write_only=True)
    company_name = serializers.CharField(required=False, allow_blank=True)

    class Meta:
        model = User
        fields = ('email', 'password', 'password2', 'full_name', 'company_name', 'phone')

    def validate(self, attrs):
        if attrs['password'] != attrs.pop('password2'):
            raise serializers.ValidationError({'password2': "Passwords don't match"})
        return attrs

    def create(self, validated_data):
        return User.objects.create_user(**validated_data)


class LoginSerializer(serializers.Serializer):
    email = serializers.EmailField()
    password = serializers.CharField()

    def validate(self, attrs):
        email = attrs['email'].lower()
        password = attrs['password']

        try:
            user = User.objects.get(email=email)
        except User.DoesNotExist:
            raise serializers.ValidationError({'error': 'Invalid email or password.'})

        if user.is_oauth_user and not user.has_usable_password():
            raise serializers.ValidationError({
                'error': f'This account uses {user.auth_provider.title()} login. Please sign in with {user.auth_provider.title()}.'
            })

        user = authenticate(email=email, password=password)
        if not user:
            raise serializers.ValidationError({'error': 'Invalid email or password.'})

        attrs['user'] = user
        return attrs


class UserSerializer(serializers.ModelSerializer):
    documents_remaining = serializers.ReadOnlyField()
    documents_limit = serializers.ReadOnlyField()
    is_oauth_user = serializers.ReadOnlyField()
    can_access_sales = serializers.ReadOnlyField()
    is_client_user = serializers.ReadOnlyField()
    is_platform_admin = serializers.ReadOnlyField()

    class Meta:
        model = User
        fields = (
            'id', 'email', 'full_name', 'phone', 'company_name', 'profile_picture',
            'subscription_plan', 'documents_used_this_month', 'documents_remaining',
            'documents_limit', 'is_oauth_user', 'auth_provider', 'created_at',
            'can_access_sales', 'sales_access_enabled', 'is_client_user', 'is_platform_admin',
            'must_change_password',
        )
        read_only_fields = (
            'id', 'email', 'auth_provider', 'created_at', 
            'can_access_sales', 'sales_access_enabled', 'is_client_user', 'is_platform_admin',
            'must_change_password',
        )


class ChangePasswordSerializer(serializers.Serializer):
    old_password = serializers.CharField()
    new_password = serializers.CharField(min_length=8)
