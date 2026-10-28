from rest_framework import generics, status
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response
from django.middleware.csrf import get_token

from django.views.decorators.csrf import csrf_protect
from django.utils.decorators import method_decorator

from .serializers import (
    LoginSerializer,
    PasswordConfirmSerializer,
    PasswordResetSerializer,
    RegisterSerializer,
)
from .cookies import clear_auth_cookies, set_auth_cookies, _set_auth_cookie

from .services import (
    activate_user,
    blacklist_refresh_token,
    complete_password_reset,
    create_access_token,
    get_activation_user,
    send_activation_email,
    send_password_reset_email,
)


class RegisterView(generics.CreateAPIView):
    serializer_class = RegisterSerializer
    permission_classes = [AllowAny]
    authentication_classes = []

    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        user = serializer.save()
        user.is_active = False
        user.save()
        token = send_activation_email(user, request)
        return Response(
            {
                "user": {"id": user.id, "email": user.email},
                "token": token,
            },
            status=status.HTTP_201_CREATED,
        )


class ActivateView(generics.GenericAPIView):

    permission_classes = [AllowAny]
    authentication_classes = []

    def get(self, request, uidb64, token):
        user = get_activation_user(uidb64)
        if user is None:
            return Response(status=status.HTTP_400_BAD_REQUEST)
        if not activate_user(user, token):
            return Response(status=status.HTTP_400_BAD_REQUEST)
        return Response(
            {"message": "Account successfully activated."},
            status=status.HTTP_200_OK,
        )


@method_decorator(csrf_protect, name='dispatch')
class LoginView(generics.GenericAPIView):
    serializer_class = LoginSerializer
    permission_classes = [AllowAny]
    authentication_classes = []

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

@method_decorator(csrf_protect, name='dispatch')
class LogoutView(generics.GenericAPIView):

    permission_classes = [AllowAny]
    authentication_classes = []

    def post(self, request, *args, **kwargs):
        refresh_token = request.COOKIES.get('refresh_token')
        if not refresh_token:
            return Response(status=status.HTTP_400_BAD_REQUEST)
        if not blacklist_refresh_token(refresh_token):
            return Response(status=status.HTTP_400_BAD_REQUEST)
        response = Response(
            {"detail": "Logout successful! All tokens will be deleted. "
                       "Refresh token is now invalid."},
            status=status.HTTP_200_OK,
        )
        return clear_auth_cookies(response)


class CSRFTokenView(generics.GenericAPIView):
    permission_classes = [AllowAny]
    authentication_classes = []

    def get(self, request, *args, **kwargs):
        csrf_token = get_token(request)

        return Response({"csrfToken": csrf_token}, status=status.HTTP_200_OK)


class AuthTestView(generics.GenericAPIView):
    permission_classes = [IsAuthenticated]

    def get(self, request, *args, **kwargs):
        return Response({"email": request.user.email}, status=status.HTTP_200_OK)

@method_decorator(csrf_protect, name='dispatch')
class TokenRefreshView(generics.GenericAPIView):
    permission_classes = [AllowAny]
    authentication_classes = []

    def post(self, request, *args, **kwargs):
        refresh_token = request.COOKIES.get('refresh_token')
        if not refresh_token:
            return Response(status=status.HTTP_400_BAD_REQUEST)
        access = create_access_token(refresh_token)
        if access is None:
            return Response(status=status.HTTP_401_UNAUTHORIZED)
        response = Response({
            "detail": "Token refreshed",
            "access": access,
        }, status=status.HTTP_200_OK)
        _set_auth_cookie(response, "access_token", access)
        return response


class PasswordResetView(generics.GenericAPIView):
    serializer_class = PasswordResetSerializer
    permission_classes = [AllowAny]
    authentication_classes = []

    def post(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        send_password_reset_email(serializer.validated_data["email"], request)
        return Response(
            {"detail": "An email has been sent to reset your password."},
            status=status.HTTP_200_OK,
        )


class PasswordConfirmView(generics.GenericAPIView):
    permission_classes = [AllowAny]
    serializer_class = PasswordConfirmSerializer
    authentication_classes = []

    def post(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        result = complete_password_reset(
            kwargs["uidb64"], kwargs["token"],
            serializer.validated_data["new_password"],
        )
        return password_reset_response(result)


def password_reset_response(result):
    messages = {
        None: "Invalid reset link.",
        False: "Invalid or expired reset link.",
        True: "Your Password has been successfully reset.",
    }
    response_status = (
        status.HTTP_200_OK if result is True else status.HTTP_400_BAD_REQUEST
    )
    return Response({"detail": messages[result]}, status=response_status)
