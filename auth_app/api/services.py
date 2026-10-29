"""Business logic for account activation, authentication, and password resets."""

from django.contrib.auth import get_user_model
from django.contrib.auth.tokens import default_token_generator
from django.core.mail import send_mail
from django.urls import reverse
from django.utils.encoding import force_bytes, force_str
from django.utils.http import urlsafe_base64_decode, urlsafe_base64_encode
from rest_framework.exceptions import AuthenticationFailed
from rest_framework_simplejwt.exceptions import TokenError
from rest_framework_simplejwt.tokens import RefreshToken


User = get_user_model()


def blacklist_refresh_token(raw_token):
    """Blacklist a refresh token, returning whether it was valid."""
    if not raw_token:
        return False
    try:
        RefreshToken(raw_token).blacklist()
    except TokenError:
        return False
    return True


def get_user_for_login(email, password):
    """Return an active user matching the credentials or raise an auth error."""
    try:
        user = User.objects.get(email=email)
    except User.DoesNotExist:
        raise AuthenticationFailed("Invalid email or password")
    if not user.check_password(password) or user.is_active is False:
        raise AuthenticationFailed("Invalid email or password")
    return user


def create_user_tokens(user):
    """Create access and refresh JWTs for a user."""
    refresh = RefreshToken.for_user(user)
    return {
        "refresh": str(refresh),
        "access": str(refresh.access_token),
        "user": user,
    }


def create_activation_link(user, request, token):
    """Build an absolute URL for activating the given user account."""
    uidb64 = urlsafe_base64_encode(force_bytes(user.pk))
    activation_path = reverse("activate", kwargs={"uidb64": uidb64, "token": token})
    return request.build_absolute_uri(activation_path)


def send_activation_email(user, request):
    """Send an activation email and return its generated token."""
    token = default_token_generator.make_token(user)
    activation_link = create_activation_link(user, request, token)
    send_mail(
        subject="Activate your Videoflix account",
        message=(
            "Welcome to Videoflix! Please activate your account by clicking "
            f"the following link {activation_link}"
        ),
        from_email="noreply@videoflix.de",
        recipient_list=[user.email],
    )
    return token


def get_activation_user(uidb64):
    """Decode a user ID and return its account, or ``None`` if it is invalid."""
    try:
        user_id = force_str(urlsafe_base64_decode(uidb64))
        return User.objects.get(pk=user_id)
    except (User.DoesNotExist, ValueError):
        return None


def activate_user(user, token):
    """Activate a user when the supplied token is valid."""
    if not default_token_generator.check_token(user, token):
        return False
    user.is_active = True
    user.save()
    return True


def create_password_reset_link(user, request):
    """Build an absolute password-reset URL for the given user."""
    token = default_token_generator.make_token(user)
    uidb64 = urlsafe_base64_encode(force_bytes(user.id))
    reset_path = reverse("password_confirm", kwargs={"uidb64": uidb64, "token": token})
    return request.build_absolute_uri(reset_path)


def send_password_reset_email(email, request):
    """Send a password-reset email when the email belongs to an account."""
    user = User.objects.filter(email=email).first()
    if user is None:
        return
    reset_link = create_password_reset_link(user, request)
    _send_password_reset_email(user, reset_link)


def _send_password_reset_email(user, reset_link):
    """Send the reset message to the user's registered email address."""
    send_mail(
        subject="Reset your Videoflix password",
        message=(
            "Hello! You requested a password reset for your Videoflix account. "
            "Please click the following link to reset your password: "
            f"{reset_link}\n\n"
            "If you did not request this, you can safely ignore this email."
        ),
        from_email="noreply@videoflix.de",
        recipient_list=[user.email],
    )


def get_password_reset_user(uidb64):
    """Decode a user ID and return its account, or ``None`` if invalid."""
    try:
        user_id = force_str(urlsafe_base64_decode(uidb64))
        return User.objects.filter(id=user_id).first()
    except (TypeError, ValueError, OverflowError):
        return None


def is_password_reset_token_valid(user, token):
    """Check that a user exists and the reset token is valid for that user."""
    return user is not None and default_token_generator.check_token(user, token)


def reset_user_password(user, password):
    """Set and persist a user's new password."""
    user.set_password(password)
    user.save()


def complete_password_reset(uidb64, token, password):
    """Reset a user's password; return ``None`` or ``False`` on failure."""
    user = get_password_reset_user(uidb64)
    if user is None:
        return None
    if not is_password_reset_token_valid(user, token):
        return False
    reset_user_password(user, password)
    return True


def create_access_token(refresh_token):
    """Return a new access token or ``None`` for an invalid refresh token."""
    try:
        return str(RefreshToken(refresh_token).access_token)
    except TokenError:
        return None