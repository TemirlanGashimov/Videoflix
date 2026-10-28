"""Cookie-based JWT authentication with CSRF protection."""

from rest_framework_simplejwt.authentication import JWTAuthentication
from rest_framework.authentication import SessionAuthentication

class CookieJWTAuthentication(JWTAuthentication):
    """Authenticate requests using an access JWT stored in a cookie."""

    def authenticate(self, request):
        """Validate the access cookie and enforce CSRF protection."""
        access_token = request.COOKIES.get('access_token')
        if not access_token:
            return None
        validated_token = self.get_validated_token(access_token)
        self.enforce_csrf(request)
        user = self.get_user(validated_token)
        return (user, validated_token)

    def enforce_csrf(self, request):
        """Apply Django REST Framework's session CSRF validation."""
        SessionAuthentication().enforce_csrf(request)