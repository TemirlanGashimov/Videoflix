"""Authentication API views for registration, sessions, and password recovery."""

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
    """Create an inactive account and send its activation email."""

    serializer_class = RegisterSerializer
    permission_classes = [AllowAny]
    authentication_classes = []

    def create(self, request, *args, **kwargs):
        """Validate registration data and return the new account and token."""
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        user = serializer.save()
        token = send_activation_email(user, request)
        if token is None:
            return Response({"detail": "Activation email could not be sent."}, status=status.HTTP_503_SERVICE_UNAVAILABLE)
        return Response(
            {
                "user": {"id": user.id, "email": user.email},
                "token": token,
            },
            status=status.HTTP_201_CREATED,
        )


class ActivateView(generics.GenericAPIView):
    """Activate an account using the UID and token from its email link."""

    permission_classes = [AllowAny]
    authentication_classes = []

    def get(self, request, uidb64, token):
        """Validate the activation link and activate its account."""
        user = get_activation_user(uidb64)
        if user is None:
            return Response(status=status.HTTP_400_BAD_REQUEST)
        if not activate_user(user, token):
            return Response(status=status.HTTP_400_BAD_REQUEST)
        return Response(
            {"message": "Account successfully activated."},
            status=status.HTTP_200_OK,
        )


class LoginView(generics.GenericAPIView):
    """Authenticate a user and set access and refresh cookies."""

    serializer_class = LoginSerializer
    permission_classes = [AllowAny]
    authentication_classes = []

    def post(self, request, *args, **kwargs):
        """Authenticate the submitted credentials and return user details."""
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
    """Invalidate the refresh token and clear authentication cookies."""

    permission_classes = [AllowAny]
    authentication_classes = []

    def post(self, request, *args, **kwargs):
        """Blacklist the refresh cookie and remove both token cookies."""
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
    """Provide a CSRF token for clients making protected requests."""

    permission_classes = [AllowAny]
    authentication_classes = []

    def get(self, request, *args, **kwargs):
        """Return the CSRF token associated with the current request."""
        csrf_token = get_token(request)

        return Response({"csrfToken": csrf_token}, status=status.HTTP_200_OK)


class AuthTestView(generics.GenericAPIView):
    """Return the email address of the authenticated user."""

    permission_classes = [IsAuthenticated]

    def get(self, request, *args, **kwargs):
        """Respond with the authenticated user's email address."""
        return Response({"email": request.user.email}, status=status.HTTP_200_OK)

@method_decorator(csrf_protect, name='dispatch')
class TokenRefreshView(generics.GenericAPIView):
    """Issue a new access token from the refresh-token cookie."""

    permission_classes = [AllowAny]
    authentication_classes = []

    def post(self, request, *args, **kwargs):
        """Refresh the access token and replace its cookie."""
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
    """Request a password-reset email for the submitted email address."""

    serializer_class = PasswordResetSerializer
    permission_classes = [AllowAny]
    authentication_classes = []

    def post(self, request, *args, **kwargs):
        """Validate the email and send a reset link when an account exists."""
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        send_password_reset_email(serializer.validated_data["email"], request)
        return Response(
            {"detail": "An email has been sent to reset your password."},
            status=status.HTTP_200_OK,
        )


class PasswordConfirmView(generics.GenericAPIView):
    """Set a new password using a UID and token from a reset link."""

    permission_classes = [AllowAny]
    serializer_class = PasswordConfirmSerializer
    authentication_classes = []

    def post(self, request, *args, **kwargs):
        """Validate the new password and complete the reset."""
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        result = complete_password_reset(
            kwargs["uidb64"], kwargs["token"],
            serializer.validated_data["new_password"],
        )
        return password_reset_response(result)


def password_reset_response(result):
    """Build the API response for a password-reset result."""
    messages = {
        None: "Invalid reset link.",
        False: "Invalid or expired reset link.",
        True: "Your Password has been successfully reset.",
    }
    response_status = (
        status.HTTP_200_OK if result is True else status.HTTP_400_BAD_REQUEST
    )
    return Response({"detail": messages[result]}, status=response_status)
