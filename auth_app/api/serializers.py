"""Request serializers and validation for the authentication API."""

from rest_framework import serializers
from django.contrib.auth import get_user_model

from django.contrib.auth.password_validation import validate_password
from django.core.exceptions import ValidationError

from .services import create_user_tokens, get_user_for_login


User = get_user_model()


class RegisterSerializer(serializers.ModelSerializer):
    """Validate registration details and create an inactive user account."""

    confirmed_password = serializers.CharField(write_only=True)

    class Meta:
        """Configure the fields exposed by the registration endpoint."""

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
        """Ensure the confirmation matches the submitted password."""
        password = self.initial_data.get('password')
        if password and value and password != value:
            raise serializers.ValidationError("Passwords do not match.")
        return value

    def validate_email(self, value):
        """Reject email addresses already associated with an account."""
        if User.objects.filter(email=value).exists():
            raise serializers.ValidationError("Email is already in use.")
        return value
    
    def validate_password(self, value):
        """Apply the configured Django password validators."""
        try:
            validate_password(value)

        except ValidationError as e:
            raise serializers.ValidationError(e.messages)

        return value

    def create(self, validated_data):
        """Create an inactive account with a securely hashed password."""
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
    """Validate login credentials and provide the user's JWT tokens."""

    email = serializers.EmailField()
    password = serializers.CharField(write_only=True)

    def validate(self, attrs):
        """Authenticate the supplied credentials and return token data."""
        user = get_user_for_login(attrs["email"], attrs["password"])
        return create_user_tokens(user)

class PasswordResetSerializer(serializers.Serializer):
    """Validate the email address used to request a password reset."""

    email = serializers.EmailField()


class PasswordConfirmSerializer(serializers.Serializer):
    """Validate and confirm a proposed password-reset value."""

    new_password = serializers.CharField(write_only=True)
    confirm_password = serializers.CharField(write_only=True)

    def validate(self, attrs):
        """Require matching passwords and enforce configured password rules."""
        new_password = attrs["new_password"]
        confirm_password = attrs["confirm_password"]

        if new_password != confirm_password:
            raise serializers.ValidationError("Passwords do not match")
        try:
            validate_password(new_password)

        except ValidationError as e:
            raise serializers.ValidationError(e.messages)

        return attrs