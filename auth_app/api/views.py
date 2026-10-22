from rest_framework import generics, status
from rest_framework.permissions import AllowAny
from rest_framework.response import Response
from rest_framework_simplejwt.tokens import RefreshToken, TokenError

from django.urls import reverse
from django.utils.http import urlsafe_base64_encode, urlsafe_base64_decode
from django.utils.encoding import force_bytes, force_str
from django.contrib.auth.tokens import default_token_generator
from django.core.mail import send_mail

from .serializers import RegisterSerializer, LoginSerializer, PasswordResetSerializer

from django.contrib.auth import get_user_model

from .services import (set_auth_cookies,
                       blacklist_refresh_token,
                       clear_auth_cookies,
                       _set_auth_cookie)

User = get_user_model()


class RegisterView(generics.CreateAPIView):
    serializer_class = RegisterSerializer
    permission_classes = [AllowAny]

    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        user = serializer.save()

        user.is_active = False
        user.save()
        uidb64 = urlsafe_base64_encode(force_bytes(user.pk))
        token = default_token_generator.make_token(user)
        activation_path = reverse(
            "activate", kwargs={"uidb64": uidb64, "token": token})
        activation_link = request.build_absolute_uri(activation_path)

        send_mail(subject="Activate your Videoflix account",
                  message=f"Welcome to Videoflix! Please activate your account by clicking the following link {activation_link}",
                  from_email="noreply@videoflix.de",
                  recipient_list=[user.email])

        return Response(
            {'user': {
                'id': user.id,
                'email': user.email
            },
                'token': token
            },
            status=status.HTTP_201_CREATED
        )


class ActivateView(generics.GenericAPIView):

    permission_classes = [AllowAny]

    def get(self, request, uidb64, token):
        try:
            uidb64 = urlsafe_base64_decode(uidb64)
            user_id = force_str(uidb64)
            user = User.objects.get(pk=user_id)

        except (User.DoesNotExist, ValueError):
            return Response(status=status.HTTP_400_BAD_REQUEST)

        if default_token_generator.check_token(user, token):
            user.is_active = True
            user.save()

            return Response({'message': 'Account successfully activated.'}, status=status.HTTP_200_OK)

        return Response(status=status.HTTP_400_BAD_REQUEST)


class LoginView(generics.GenericAPIView):
    serializer_class = LoginSerializer
    permission_classes = [AllowAny]

    def post(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        refresh = serializer.validated_data['refresh']
        access = serializer.validated_data['access']
        user = serializer.validated_data['user']
        user_data = {"id": user.id, "username": user.username, }
        response = Response(
            {"detail": "Login successful", "user": user_data},
            status=status.HTTP_200_OK
        )
        return set_auth_cookies(response, access, refresh)


class LogoutView(generics.GenericAPIView):

    permission_classes = [AllowAny]

    def post(self, request, *args, **kwargs):
        refresh_token = request.COOKIES.get('refresh_token')
        if not refresh_token:
            return Response(status=status.HTTP_400_BAD_REQUEST)

        success = blacklist_refresh_token(refresh_token)
        if not success:
            return Response(status=status.HTTP_400_BAD_REQUEST)

        response = Response(
            {"detail": "Logout successful! All tokens will be deleted. Refresh token is now invalid."},
            status=status.HTTP_200_OK,
        )
        return clear_auth_cookies(response)


class TokenRefreshView(generics.GenericAPIView):
    permission_classes = [AllowAny]

    def post(self, request, *args, **kwargs):
        refresh_token = request.COOKIES.get('refresh_token')
        if not refresh_token:
            return Response(status=status.HTTP_400_BAD_REQUEST,
                            )
        try:
            refresh = RefreshToken(refresh_token)
            access = refresh.access_token

        except TokenError:
            return Response(status=status.HTTP_401_UNAUTHORIZED)

        response = Response({
            "detail": "Token refreshed",
            "access": str(access),
        }, status=status.HTTP_200_OK)
        _set_auth_cookie(response, "access_token", access)
        return response


class PasswordResetView(generics.GenericAPIView):
    serializer_class = PasswordResetSerializer
    permission_classes = [AllowAny]

    def post(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        email = serializer.validated_data['email']
        user = User.objects.filter(email=email).first()
        if user is not None:
            token = default_token_generator.make_token(user)
            user_id = force_bytes(user.id)
            uidb64 = urlsafe_base64_encode(user_id)
            reset_path = reverse("password_confirm", kwargs={
                                 "uidb64": uidb64, "token": token})
            reset_link = request.build_absolute_uri(reset_path)
            send_mail(subject="Reset your Videoflix password",
                      message=f"Hello! You requested a password reset for your Videoflix account. Please click the following link to reset your password: {reset_link}\n\nIf you did not request this, you can safely ignore this email.",
                      from_email="noreply@videoflix.de",
                      recipient_list=[user.email])
        response = Response ({"detail": "An email has been sent to reset your password."}, status=status.HTTP_200_OK)
        return response

class PasswordConfirmView(generics.GenericAPIView):
    permission_classes = [AllowAny]

    def post(self, request, *args, **kwargs):
        pass