from rest_framework import serializers
from django.contrib.auth import get_user_model

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



