from rest_framework import serializers
from django.contrib.auth import get_user_model

from rest_framework_simplejwt.tokens import RefreshToken
from rest_framework.exceptions import AuthenticationFailed
from django.contrib.auth import authenticate
from django.contrib.auth.password_validation import validate_password
from django.core.exceptions import ValidationError


User = get_user_model()


class RegisterSerializer(serializers.ModelSerializer):
    confirmed_password = serializers.CharField(write_only=True)

    class Meta:
        model = User
        fields = ['id', 'username', 'email', 'password', 'confirmed_password']
        read_only_fields = ['id']
        extra_kwargs = {
            'password': {
                'write_only': True
                },
            'email': {
                'required': True
            }
        }

    def validate_confirmed_password(self, value):
        password = self.initial_data.get('password')
        if password and value and password != value:
            raise serializers.ValidationError("Passwords do not match.")
        return value

    def validate_email(self, value):
        if User.objects.filter(email=value).exists():
            raise serializers.ValidationError("Email is already in use.")
        return value
    
    def validate_password(self, value):
        try:
            validate_password(value)

        except ValidationError as e:
            raise serializers.ValidationError(e.messages)

        return value

    def create(self, validated_data):
        password = validated_data.pop('password')
        validated_data.pop('confirmed_password')

        account = User(
            email=self.validated_data['email'],
            username=self.validated_data['username'],
        )
        account.is_active = False

        account.set_password(password)
        account.save()

        return account

class LoginSerializer(serializers.Serializer):

    email = serializers.EmailField()
    password = serializers.CharField(write_only=True)

    def validate(self, attrs):
        email = attrs["email"]
        password = attrs["password"]
    
        try:
            user = User.objects.get(email=email)
        except User.DoesNotExist:
            raise AuthenticationFailed("Invalid email or password")
        if not user.check_password(password):
            raise AuthenticationFailed("Invalid email or password")

        if user.is_active is False:
            raise AuthenticationFailed("Invalid email or password")

        refresh = RefreshToken.for_user(user)

        return {
            'refresh': str(refresh),
            'access': str(refresh.access_token),
            'user': user
        }

class PasswordResetSerializer(serializers.Serializer):

    email = serializers.EmailField()


class PasswordConfirmSerializer(serializers.Serializer):

    new_password = serializers.CharField(write_only=True)
    confirm_password = serializers.CharField(write_only=True)

    def validate(self, attrs):
        new_password = attrs["new_password"]
        confirm_password = attrs["confirm_password"]

        if new_password != confirm_password:
            raise serializers.ValidationError("Passwords do not match")
        try:
            validate_password(new_password)

        except ValidationError as e:
            raise serializers.ValidationError(e.messages)

        return attrs